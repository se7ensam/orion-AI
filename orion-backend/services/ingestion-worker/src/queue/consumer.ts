import { connect, ConsumeMessage } from 'amqplib';
import { ENV } from '../config/env.js';
import { QUEUE_NAME, IngestionJob } from '@orion/shared';
import { SecDownloader } from '../sec-client/downloader.js';
import { cleanHtml } from '../processor/html-cleaner.js';
import { Chunker } from '../processor/chunker.js';
import { IngestionRepository } from '../store/repository.js';

export class IngestionConsumer {
    private connection: any; // amqplib.Connection
    private channel: any; // amqplib.Channel
    private downloader: SecDownloader;
    private repository: IngestionRepository;

    constructor() {
        this.downloader = new SecDownloader();
        this.repository = new IngestionRepository();
    }

    async start() {
        console.log('Connecting to RabbitMQ...');
        try {
            this.connection = await connect(ENV.RABBITMQ_URL);
            if (!this.connection) {
                throw new Error('Failed to connect to RabbitMQ');
            }
            this.channel = await this.connection.createChannel();
            if (!this.channel) {
                throw new Error('Failed to create channel');
            }

            await this.channel.assertQueue(QUEUE_NAME, { durable: true });
            await this.channel.prefetch(1); // Process 1 message at a time

            console.log(`Waiting for messages in ${QUEUE_NAME}...`);
            this.channel.consume(QUEUE_NAME, this.handleMessage.bind(this), { noAck: false });
        } catch (error) {
            console.error('Failed to start consumer:', error);
            throw error;
        }
    }

    private async handleMessage(msg: ConsumeMessage | null) {
        if (!msg) return;

        let job: IngestionJob;
        try {
            job = JSON.parse(msg.content.toString());
        } catch (parseError) {
            console.error('❌ Failed to parse job message:', parseError);
            this.channel?.nack(msg, false, false); // Don't requeue invalid messages
            return;
        }

        const startTime = Date.now();
        try {
            // 1. Download
            const rawHtml = await this.downloader.downloadHtml(job.url);

            // 2. Process (free rawHtml from memory as soon as possible)
            const cleanText = cleanHtml(rawHtml);
            const chunks = Chunker.chunkText(cleanText);

            // 3. Store (save rawHtml to DB, then we can free it)
            const filingId = await this.repository.saveFiling(job, rawHtml);
            await this.repository.saveChunks(filingId, chunks);
            await this.repository.updateStatus(filingId, 'COMPLETED');

            this.channel?.ack(msg);
            
            const duration = Date.now() - startTime;
            if (duration > 5000) { // Only log slow jobs (>5s)
                console.log(`Job for CIK ${job.cik} completed in ${duration}ms (${chunks.length} chunks)`);
            }
        } catch (error: unknown) {
            const errorMessage = error instanceof Error ? error.message : String(error);
            
            // Handle rate limit errors - requeue the message for later
            if (errorMessage.includes('Rate limit') || errorMessage.includes('429')) {
                console.error(`⚠️  Rate limit error for CIK ${job?.cik || 'unknown'}: ${errorMessage}`);
                // Reject and requeue - RabbitMQ will redeliver after a delay
                this.channel?.nack(msg, false, true); // requeue = true
                return;
            }

            // Handle other errors
            console.error(`❌ Error processing job for CIK ${job?.cik || 'unknown'}:`, errorMessage);
            // Reject without requeue - message goes to dead letter queue or is lost
            this.channel?.nack(msg, false, false); // requeue = false
        }
    }
}
