import { connect } from 'amqplib';
import { QUEUE_NAME } from '@orion/shared';
import * as dotenv from 'dotenv';
import * as readline from 'readline';
dotenv.config();

const RABBITMQ_URL = process.env.RABBITMQ_URL || 'amqp://localhost';

/**
 * Ask for user confirmation before purging
 */
async function askConfirmation(messageCount: number): Promise<boolean> {
    const rl = readline.createInterface({
        input: process.stdin,
        output: process.stdout
    });

    return new Promise((resolve) => {
        rl.question(
            `⚠️  Are you sure you want to purge ${messageCount} message(s) from "${QUEUE_NAME}"? (yes/no): `,
            (answer) => {
                rl.close();
                resolve(answer.toLowerCase() === 'yes' || answer.toLowerCase() === 'y');
            }
        );
    });
}

async function main() {
    console.log(`Connecting to RabbitMQ...`);
    
    try {
        const connection = await connect(RABBITMQ_URL);
        const channel = await connection.createChannel();

        // Check queue exists and get message count
        const queue = await channel.checkQueue(QUEUE_NAME);
        const messageCount = queue.messageCount;
        const consumerCount = queue.consumerCount;

        console.log(`\n═══════════════════════════════════════`);
        console.log(`Queue: ${QUEUE_NAME}`);
        console.log(`═══════════════════════════════════════`);
        console.log(`Messages:  ${messageCount.toLocaleString()}`);
        console.log(`Consumers: ${consumerCount}`);
        console.log(`═══════════════════════════════════════\n`);

        if (messageCount === 0) {
            console.log('✓ Queue is already empty. Nothing to purge.');
            await channel.close();
            await connection.close();
            return;
        }

        // Warn if consumers are active
        if (consumerCount > 0) {
            console.log(`⚠️  Warning: ${consumerCount} consumer(s) are currently active.`);
            console.log(`   Purging will remove messages they might be processing.\n`);
        }

        // Ask for confirmation
        const confirmed = await askConfirmation(messageCount);

        if (!confirmed) {
            console.log('❌ Purge cancelled.');
            await channel.close();
            await connection.close();
            return;
        }

        console.log(`\nPurging ${messageCount.toLocaleString()} messages from ${QUEUE_NAME}...`);
        const startTime = Date.now();

        const purgeResult = await channel.purgeQueue(QUEUE_NAME);
        
        const duration = Date.now() - startTime;
        
        console.log(`\n✓ Successfully purged ${purgeResult.messageCount.toLocaleString()} messages`);
        console.log(`  Duration: ${duration}ms`);

        // Verify queue is empty
        const verifyQueue = await channel.checkQueue(QUEUE_NAME);
        if (verifyQueue.messageCount === 0) {
            console.log(`  Verification: Queue is now empty ✓`);
        } else {
            console.log(`  ⚠️  Warning: ${verifyQueue.messageCount} messages remain (may be in-flight)`);
        }

        await channel.close();
        await connection.close();

    } catch (error: unknown) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        console.error(`\n❌ Error purging queue: ${errorMessage}`);
        
        if (errorMessage.includes('NOT_FOUND')) {
            console.error(`   Queue "${QUEUE_NAME}" does not exist.`);
        } else if (errorMessage.includes('ECONNREFUSED')) {
            console.error(`   Cannot connect to RabbitMQ at ${RABBITMQ_URL}`);
            console.error(`   Make sure RabbitMQ is running.`);
        }
        
        process.exit(1);
    }
}

main().catch(error => {
    console.error('Unexpected error:', error);
    process.exit(1);
});
