import { connect, ConsumeMessage } from 'amqplib';
import type { Connection, Channel } from 'amqplib';
import { Pool } from 'pg';
import { ENV } from '../config/env.js';
import { QUEUE_NAME, IngestionJob } from '@orion/shared';
import { SecDownloader } from '../sec-client/downloader.js';
import { cleanHtml } from '../processor/html-cleaner.js';
import { Chunker } from '../processor/chunker.js';
import { IngestionRepository } from '../store/repository.js';
import { metricsCollector } from '../monitoring/metrics.js';

export class IngestionConsumer {
    private connection: any = null; // amqplib Connection
    private channel: any = null; // amqplib Channel
    private downloader: SecDownloader;
    private repository: IngestionRepository;
    private pool: Pool;
    private consumerTag: string | null = null;
    private isShuttingDown: boolean = false;
    private metricsInterval: NodeJS.Timeout | null = null;

    constructor() {
        // Create shared connection pool for better resource management
        this.pool = new Pool({ 
            connectionString: ENV.DATABASE_URL,
            max: 20,
            idleTimeoutMillis: 30000,
            connectionTimeoutMillis: 2000,
        });

        this.downloader = new SecDownloader();
        this.repository = new IngestionRepository(this.pool);

        // Setup graceful shutdown handlers
        this.setupShutdownHandlers();

        // Start periodic metrics reporting (every 5 minutes)
        this.startMetricsReporting();
    }

    private setupShutdownHandlers() {
        process.on('SIGTERM', () => {
            console.log('Received SIGTERM signal');
            this.shutdown();
        });
        
        process.on('SIGINT', () => {
            console.log('Received SIGINT signal');
            this.shutdown();
        });

        process.on('uncaughtException', (error) => {
            console.error('Uncaught exception:', error);
            this.shutdown();
        });

        process.on('unhandledRejection', (reason, promise) => {
            console.error('Unhandled rejection at:', promise, 'reason:', reason);
            this.shutdown();
        });
    }

    private startMetricsReporting() {
        // Report metrics every 5 minutes
        this.metricsInterval = setInterval(() => {
            metricsCollector.printSummary();
            
            // Log pool stats
            const poolStats = this.repository.getPoolStats();
            console.log(`📊 DB Pool: ${poolStats.idleCount}/${poolStats.totalCount} idle, ${poolStats.waitingCount} waiting\n`);
        }, 5 * 60 * 1000);
    }

    async start() {
        console.log('Connecting to RabbitMQ...');
        try {
            this.connection = await connect(ENV.RABBITMQ_URL);
            if (!this.connection) {
                throw new Error('Failed to connect to RabbitMQ');
            }

            // Handle connection errors
            this.connection.on('error', (err: Error) => {
                console.error('RabbitMQ connection error:', err);
                if (!this.isShuttingDown) {
                    this.shutdown();
                }
            });

            this.connection.on('close', () => {
                console.log('RabbitMQ connection closed');
                if (!this.isShuttingDown) {
                    this.shutdown();
                }
            });

            this.channel = await this.connection.createChannel();
            if (!this.channel) {
                throw new Error('Failed to create channel');
            }

            await this.channel.assertQueue(QUEUE_NAME, { durable: true });
            await this.channel.prefetch(1); // Process 1 message at a time

            console.log(`Waiting for messages in ${QUEUE_NAME}...`);
            const consumeResult = await this.channel.consume(
                QUEUE_NAME, 
                this.handleMessage.bind(this), 
                { noAck: false }
            );
            
            this.consumerTag = consumeResult.consumerTag;
        } catch (error) {
            console.error('Failed to start consumer:', error);
            throw error;
        }
    }

    private async handleMessage(msg: ConsumeMessage | null) {
        if (!msg) return;

        // Don't process new messages during shutdown
        if (this.isShuttingDown) {
            this.channel?.nack(msg, false, true); // Requeue for another worker
            return;
        }

        let job: IngestionJob;
        try {
            job = JSON.parse(msg.content.toString());
        } catch (parseError) {
            console.error('❌ Failed to parse job message:', parseError);
            this.channel?.nack(msg, false, false); // Don't requeue invalid messages
            metricsCollector.recordFailure(false);
            return;
        }

        const startTime = Date.now();
        const timings = { download: 0, cleaning: 0, chunking: 0, storage: 0 };
        
        try {
            // 1. Download
            const downloadStart = Date.now();
            let rawHtml = await this.downloader.downloadHtml(job.url);
            timings.download = Date.now() - downloadStart;
            const rawHtmlSize = rawHtml.length;

            // 2. Clean HTML
            const cleanStart = Date.now();
            const cleanText = cleanHtml(rawHtml);
            timings.cleaning = Date.now() - cleanStart;
            const cleanTextSize = cleanText.length;

            // 3. Chunk text
            const chunkStart = Date.now();
            const chunks = Chunker.chunkText(cleanText);
            timings.chunking = Date.now() - chunkStart;

            // 4. Store in a single transaction for data integrity
            const storageStart = Date.now();
            await this.repository.saveFilingWithChunks(job, rawHtml, chunks);
            timings.storage = Date.now() - storageStart;

            // 5. Free memory explicitly (allow GC to reclaim large HTML)
            rawHtml = '';

            this.channel?.ack(msg);
            
            const totalTime = Date.now() - startTime;
            
            // Record metrics
            metricsCollector.recordJob({
                downloadTimeMs: timings.download,
                cleaningTimeMs: timings.cleaning,
                chunkingTimeMs: timings.chunking,
                storageTimeMs: timings.storage,
                totalTimeMs: totalTime,
                chunksCreated: chunks.length,
                rawHtmlSize,
                cleanTextSize,
            });
            
            // Log slow jobs with detailed timing breakdown
            if (totalTime > 5000) {
                console.log(
                    `✓ CIK ${job.cik}: ${totalTime}ms total ` +
                    `(download: ${timings.download}ms, clean: ${timings.cleaning}ms, ` +
                    `chunk: ${timings.chunking}ms, store: ${timings.storage}ms) - ${chunks.length} chunks`
                );
            }
        } catch (error: unknown) {
            const errorMessage = error instanceof Error ? error.message : String(error);
            
            // Handle rate limit errors - requeue the message for later
            if (errorMessage.includes('Rate limit') || errorMessage.includes('429')) {
                console.error(`⚠️  Rate limit error for CIK ${job?.cik || 'unknown'}: ${errorMessage}`);
                metricsCollector.recordFailure(true);
                // Reject and requeue - RabbitMQ will redeliver after a delay
                this.channel?.nack(msg, false, true); // requeue = true
                return;
            }

            // Handle other errors
            console.error(`❌ Error processing job for CIK ${job?.cik || 'unknown'}:`, errorMessage);
            metricsCollector.recordFailure(false);
            // Reject without requeue - message goes to dead letter queue or is lost
            this.channel?.nack(msg, false, false); // requeue = false
        }
    }

    /**
     * Gracefully shutdown the consumer.
     * Waits for in-flight messages to complete before closing connections.
     */
    private async shutdown() {
        if (this.isShuttingDown) {
            return; // Already shutting down
        }

        this.isShuttingDown = true;
        console.log('Initiating graceful shutdown...');

        try {
            // Stop metrics reporting
            if (this.metricsInterval) {
                clearInterval(this.metricsInterval);
            }

            // Print final metrics summary
            console.log('\n📊 Final Metrics Summary:');
            metricsCollector.printSummary();

            // Stop consuming new messages
            if (this.channel && this.consumerTag) {
                console.log('Cancelling consumer...');
                await this.channel.cancel(this.consumerTag);
            }

            // Give in-flight messages time to complete (max 5 seconds)
            console.log('Waiting for in-flight messages to complete...');
            await new Promise(resolve => setTimeout(resolve, 5000));

            // Close RabbitMQ channel
            if (this.channel) {
                console.log('Closing RabbitMQ channel...');
                await this.channel.close();
            }

            // Close RabbitMQ connection
            if (this.connection) {
                console.log('Closing RabbitMQ connection...');
                await this.connection.close();
            }

            // Close database pool
            console.log('Closing database connection pool...');
            await this.repository.close();

            console.log('Graceful shutdown complete');
            process.exit(0);
        } catch (error) {
            console.error('Error during shutdown:', error);
            process.exit(1);
        }
    }
}
