import { IngestionConsumer } from './queue/consumer.js';
import { ENV } from './config/env.js';

/**
 * Main entry point for the ingestion worker service.
 * Handles startup, configuration validation, and graceful error handling.
 */

function printStartupBanner(): void {
    console.log('');
    console.log('═══════════════════════════════════════════════════════════');
    console.log('   🚀 ORION INGESTION WORKER');
    console.log('═══════════════════════════════════════════════════════════');
    console.log(`   Version:     2.0`);
    console.log(`   Environment: ${ENV.NODE_ENV}`);
    console.log(`   Node:        ${process.version}`);
    console.log(`   Platform:    ${process.platform}`);
    console.log('═══════════════════════════════════════════════════════════');
    console.log('');
}

function printConfiguration(): void {
    console.log('Configuration:');
    console.log(`  RabbitMQ:    ${ENV.RABBITMQ_URL}`);
    console.log(`  Database:    ${ENV.DATABASE_URL.replace(/:[^:@]+@/, ':****@')}`); // Mask password
    console.log(`  SEC API:     ${ENV.SEC_API_BASE}`);
    console.log(`  User-Agent:  ${ENV.USER_AGENT.substring(0, 50)}${ENV.USER_AGENT.length > 50 ? '...' : ''}`);
    console.log('');
}

async function startWorker(): Promise<void> {
    try {
        printStartupBanner();
        printConfiguration();

        const consumer = new IngestionConsumer();
        await consumer.start();

        console.log('✓ Worker started successfully and ready to process jobs\n');

    } catch (error: unknown) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        console.error('\n❌ Failed to start worker:', errorMessage);
        
        // Provide helpful error messages
        if (errorMessage.includes('ECONNREFUSED')) {
            console.error('\n   Cannot connect to RabbitMQ or PostgreSQL.');
            console.error('   Make sure services are running:');
            console.error('     docker-compose up -d\n');
        } else if (errorMessage.includes('ENOTFOUND')) {
            console.error('\n   DNS resolution failed.');
            console.error('   Check your connection URLs in .env file.\n');
        } else if (errorMessage.includes('authentication')) {
            console.error('\n   Authentication failed.');
            console.error('   Check your credentials in DATABASE_URL.\n');
        }
        
        process.exit(1);
    }
}

// Handle uncaught errors at startup
process.on('unhandledRejection', (reason) => {
    console.error('Unhandled rejection during startup:', reason);
    process.exit(1);
});

// Start the worker
startWorker();
