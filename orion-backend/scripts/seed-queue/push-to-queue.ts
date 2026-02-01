import amqp from 'amqplib';
import fs from 'fs-extra';
import path from 'path';
import { QUEUE_NAME, IngestionJob } from '@orion/shared';
import * as dotenv from 'dotenv';
dotenv.config();

const INPUT_FILE = path.join(process.cwd(), 'filings-6k.json');
const RABBITMQ_URL = process.env.RABBITMQ_URL || 'amqp://localhost';
const BATCH_SIZE = 100; // Process in batches for better memory management

async function main() {
    console.log('Reading filings from file...');
    const filings: IngestionJob[] = await fs.readJson(INPUT_FILE);

    if (filings.length === 0) {
        console.log('No filings found in input file.');
        return;
    }

    console.log(`Pushing ${filings.length} jobs to queue in batches of ${BATCH_SIZE}...`);

    const connection = await amqp.connect(RABBITMQ_URL);
    const channel = await connection.createChannel();
    await channel.assertQueue(QUEUE_NAME, { durable: true });

    const startTime = Date.now();
    let pushedCount = 0;

    // Process in batches to avoid overwhelming RabbitMQ and manage memory better
    for (let i = 0; i < filings.length; i += BATCH_SIZE) {
        const batch = filings.slice(i, Math.min(i + BATCH_SIZE, filings.length));
        
        // Push batch
        for (const filing of batch) {
            const success = channel.sendToQueue(
                QUEUE_NAME, 
                Buffer.from(JSON.stringify(filing)), 
                { persistent: true }
            );
            
            if (!success) {
                // Buffer is full, wait for drain event
                await new Promise(resolve => channel.once('drain', resolve));
                // Retry this filing
                channel.sendToQueue(
                    QUEUE_NAME, 
                    Buffer.from(JSON.stringify(filing)), 
                    { persistent: true }
                );
            }
            
            pushedCount++;
        }

        // Progress indicator
        const progress = ((i + batch.length) / filings.length * 100).toFixed(1);
        process.stdout.write(`\rProgress: ${progress}% (${pushedCount}/${filings.length})`);
    }

    console.log('\n');

    const duration = Date.now() - startTime;
    const rate = Math.round(pushedCount / (duration / 1000));
    
    console.log(`✓ Successfully pushed ${pushedCount} jobs in ${duration}ms (${rate} jobs/sec)`);
    
    await channel.close();
    await connection.close();
}

main().catch(error => {
    console.error('Error pushing jobs to queue:', error);
    process.exit(1);
});
