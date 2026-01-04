import { connect } from 'amqplib';
import { QUEUE_NAME } from '@orion/shared';
import * as dotenv from 'dotenv';
dotenv.config();

const RABBITMQ_URL = process.env.RABBITMQ_URL || 'amqp://localhost';

async function main() {
    console.log(`Purging queue ${QUEUE_NAME}...`);
    const connection = await connect(RABBITMQ_URL);
    const channel = await connection.createChannel();

    const purged = await channel.purgeQueue(QUEUE_NAME);
    console.log(`Purged ${purged.messageCount} messages from ${QUEUE_NAME}`);

    await channel.close();
    await connection.close();
}

main().catch(console.error);
