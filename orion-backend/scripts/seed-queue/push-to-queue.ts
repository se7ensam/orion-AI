import amqp from 'amqplib';
import fs from 'fs-extra';
import path from 'path';
import { QUEUE_NAME, IngestionJob } from '@orion/shared';
import * as dotenv from 'dotenv';
dotenv.config();

const INPUT_FILE = path.join(process.cwd(), 'filings-6k.json');
const RABBITMQ_URL = process.env.RABBITMQ_URL || 'amqp://localhost';

async function main() {
    const filings: IngestionJob[] = await fs.readJson(INPUT_FILE);

    console.log(`Pushing ${filings.length} jobs to queue...`);

    const connection = await amqp.connect(RABBITMQ_URL);
    const channel = await connection.createChannel();
    await channel.assertQueue(QUEUE_NAME, { durable: true });

    for (const filing of filings) {
        channel.sendToQueue(QUEUE_NAME, Buffer.from(JSON.stringify(filing)), { persistent: true });
    }

    console.log('Done.');
    await channel.close();
    await connection.close();
}

main().catch(console.error);
