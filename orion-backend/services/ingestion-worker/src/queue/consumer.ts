import { connect, ConsumeMessage } from 'amqplib';
import { ENV } from '../config/env.js';
import { QUEUE_NAME, IngestionJob } from '@orion/shared';
import { SecDownloader } from '../sec-client/downloader.js';
import { cleanHtml } from '../processor/html-cleaner.js';
import { Chunker } from '../processor/chunker.js';
import { IngestionRepository } from '../store/repository.js';

export class IngestionConsumer {
    private connection: any;
    private channel: any;
    private downloader: SecDownloader;
    private repository: IngestionRepository;

    constructor() {
        this.downloader = new SecDownloader();
        this.repository = new IngestionRepository();
    }

    async start() {
        console.log('Connecting to RabbitMQ...');
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
        this.channel.consume(QUEUE_NAME, this.handleMessage.bind(this));
    }

    private async handleMessage(msg: ConsumeMessage | null) {
        if (!msg) return;

        try {
            const job: IngestionJob = JSON.parse(msg.content.toString());
            console.log(`Received job for ${job.cik}`);

            // 1. Download
            const rawHtml = await this.downloader.downloadHtml(job.url);

            // 2. Process
            const cleanText = cleanHtml(rawHtml);
            const chunks = Chunker.chunkText(cleanText);

            // 3. Store
            const filingId = await this.repository.saveFiling(job, rawHtml);
            await this.repository.saveChunks(filingId, chunks);
            await this.repository.updateStatus(filingId, 'COMPLETED');

            this.channel?.ack(msg);
            console.log(`Job for ${job.cik} completed.`);
        } catch (error) {
            console.error('Error processing message:', error);
            // In a real app, handle retry logic / dead letter queue
            this.channel?.nack(msg);
        }
    }
}
