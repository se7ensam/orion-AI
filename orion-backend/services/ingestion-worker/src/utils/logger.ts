/**
 * Structured logging utility for better observability and debugging.
 * Replaces raw console.log with structured, leveled logging.
 */

export enum LogLevel {
    DEBUG = 0,
    INFO = 1,
    WARN = 2,
    ERROR = 3,
}

interface LogContext {
    [key: string]: unknown;
}

class Logger {
    private minLevel: LogLevel;
    private serviceName: string;

    constructor(serviceName: string = 'ingestion-worker', minLevel: LogLevel = LogLevel.INFO) {
        this.serviceName = serviceName;
        this.minLevel = process.env.LOG_LEVEL 
            ? this.parseLogLevel(process.env.LOG_LEVEL) 
            : minLevel;
    }

    private parseLogLevel(level: string): LogLevel {
        const normalized = level.toUpperCase();
        switch (normalized) {
            case 'DEBUG': return LogLevel.DEBUG;
            case 'INFO': return LogLevel.INFO;
            case 'WARN': return LogLevel.WARN;
            case 'ERROR': return LogLevel.ERROR;
            default: return LogLevel.INFO;
        }
    }

    private shouldLog(level: LogLevel): boolean {
        return level >= this.minLevel;
    }

    private formatLog(level: string, message: string, context?: LogContext): string {
        const timestamp = new Date().toISOString();
        const logObject = {
            timestamp,
            level,
            service: this.serviceName,
            message,
            ...context,
        };

        // In production, output JSON for log aggregation
        if (process.env.NODE_ENV === 'production') {
            return JSON.stringify(logObject);
        }

        // In development, pretty print
        const contextStr = context ? ` ${JSON.stringify(context)}` : '';
        return `[${timestamp}] ${level.padEnd(5)} ${message}${contextStr}`;
    }

    debug(message: string, context?: LogContext): void {
        if (!this.shouldLog(LogLevel.DEBUG)) return;
        console.log(this.formatLog('DEBUG', message, context));
    }

    info(message: string, context?: LogContext): void {
        if (!this.shouldLog(LogLevel.INFO)) return;
        console.log(this.formatLog('INFO', message, context));
    }

    warn(message: string, context?: LogContext): void {
        if (!this.shouldLog(LogLevel.WARN)) return;
        console.warn(this.formatLog('WARN', message, context));
    }

    error(message: string, error?: Error | unknown, context?: LogContext): void {
        if (!this.shouldLog(LogLevel.ERROR)) return;
        
        const errorContext = error instanceof Error ? {
            error: error.message,
            stack: error.stack,
            ...context,
        } : { error: String(error), ...context };

        console.error(this.formatLog('ERROR', message, errorContext));
    }

    /**
     * Log job processing metrics
     */
    metric(metricName: string, value: number, unit: string, context?: LogContext): void {
        if (!this.shouldLog(LogLevel.INFO)) return;
        
        this.info(`Metric: ${metricName}`, {
            metric: metricName,
            value,
            unit,
            ...context,
        });
    }

    /**
     * Log duration of an operation
     */
    async time<T>(operation: string, fn: () => Promise<T>, context?: LogContext): Promise<T> {
        const start = Date.now();
        try {
            const result = await fn();
            const duration = Date.now() - start;
            this.metric(operation, duration, 'ms', context);
            return result;
        } catch (error) {
            const duration = Date.now() - start;
            this.error(`${operation} failed after ${duration}ms`, error, context);
            throw error;
        }
    }
}

// Export singleton instance
export const logger = new Logger('ingestion-worker');

// Export for testing or custom instances
export { Logger };
