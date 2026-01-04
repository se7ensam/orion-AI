import { IngestionConsumer } from './queue/consumer.js';

const consumer = new IngestionConsumer();

consumer.start().catch(err => {
    console.error('Failed to start worker:', err);
    process.exit(1);
});
