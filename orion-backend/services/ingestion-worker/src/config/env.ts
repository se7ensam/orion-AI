import dotenv from 'dotenv';
dotenv.config();

/**
 * Environment variable configuration with validation.
 * Ensures all required configuration is present before starting.
 */

interface EnvConfig {
    RABBITMQ_URL: string;
    DATABASE_URL: string;
    SEC_API_BASE: string;
    USER_AGENT: string;
    NODE_ENV: string;
}

/**
 * Validate that USER_AGENT follows SEC.gov requirements
 * Must include contact information
 */
function validateUserAgent(userAgent: string): void {
    if (!userAgent || userAgent.length < 10) {
        throw new Error(
            'USER_AGENT must be at least 10 characters and include contact information.\n' +
            'SEC.gov requires a User-Agent with contact info.\n' +
            'Example: OrionData/1.0 (your-email@example.com)'
        );
    }

    // Check for email or URL (basic validation)
    if (!userAgent.includes('@') && !userAgent.includes('http')) {
        console.warn(
            '⚠️  USER_AGENT should include contact information (email or URL).\n' +
            '   SEC.gov may block requests without proper identification.'
        );
    }
}

/**
 * Validate database URL format
 */
function validateDatabaseUrl(url: string): void {
    if (!url.startsWith('postgres://') && !url.startsWith('postgresql://')) {
        throw new Error(
            'DATABASE_URL must be a valid PostgreSQL connection string.\n' +
            'Example: postgres://user:password@localhost:5432/dbname'
        );
    }
}

/**
 * Validate RabbitMQ URL format
 */
function validateRabbitMqUrl(url: string): void {
    if (!url.startsWith('amqp://') && !url.startsWith('amqps://')) {
        throw new Error(
            'RABBITMQ_URL must be a valid AMQP connection string.\n' +
            'Example: amqp://localhost:5672'
        );
    }
}

/**
 * Load and validate environment configuration
 */
function loadEnv(): EnvConfig {
    const config: EnvConfig = {
        RABBITMQ_URL: process.env.RABBITMQ_URL || 'amqp://localhost',
        DATABASE_URL: process.env.DATABASE_URL || 'postgres://localhost/orion',
        SEC_API_BASE: process.env.SEC_API_BASE || 'https://www.sec.gov/Archives',
        USER_AGENT: process.env.USER_AGENT || 'OrionData/1.0 (contact@example.com)',
        NODE_ENV: process.env.NODE_ENV || 'development',
    };

    // Validate configuration
    try {
        validateUserAgent(config.USER_AGENT);
        validateDatabaseUrl(config.DATABASE_URL);
        validateRabbitMqUrl(config.RABBITMQ_URL);
    } catch (error) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        console.error('\n❌ Configuration Error:');
        console.error(errorMessage);
        console.error('\nPlease check your .env file or environment variables.\n');
        process.exit(1);
    }

    // Warn about production without custom USER_AGENT
    if (config.NODE_ENV === 'production' && config.USER_AGENT.includes('contact@example.com')) {
        console.warn(
            '\n⚠️  WARNING: Running in production with default USER_AGENT.\n' +
            '   Please set a custom USER_AGENT in your environment variables.\n'
        );
    }

    return config;
}

export const ENV = loadEnv();
