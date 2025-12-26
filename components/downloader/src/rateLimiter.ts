/**
 * Thread-safe rate limiter for SEC EDGAR requests
 * Uses a queue-based approach to ensure requests are properly serialized
 */

export class RateLimiter {
    private minInterval: number;
    private lastRequestTime: number;
    private queue: Array<() => void>;
    private processing: boolean;

    constructor(maxRate: number = 10) {
        this.minInterval = 1000 / maxRate; // milliseconds
        this.lastRequestTime = 0;
        this.queue = [];
        this.processing = false;
    }

    /**
     * Wait if necessary to respect rate limit
     * Uses a queue to ensure requests are serialized properly
     */
    async wait(): Promise<void> {
        return new Promise((resolve) => {
            this.queue.push(resolve);
            this.processQueue();
        });
    }

    /**
     * Process the queue of waiting requests
     */
    private processQueue(): void {
        if (this.processing || this.queue.length === 0) {
            return;
        }

        this.processing = true;
        this.processNext();
    }

    /**
     * Process the next request in the queue
     */
    private processNext(): void {
        if (this.queue.length === 0) {
            this.processing = false;
            return;
        }

        const now = Date.now();
        const elapsed = now - this.lastRequestTime;
        
        if (elapsed < this.minInterval) {
            const waitTime = this.minInterval - elapsed;
            setTimeout(() => {
                this.lastRequestTime = Date.now();
                const resolve = this.queue.shift();
                if (resolve) {
                    resolve();
                }
                this.processNext();
            }, waitTime);
        } else {
            this.lastRequestTime = Date.now();
            const resolve = this.queue.shift();
            if (resolve) {
                resolve();
            }
            // Process next immediately if queue is not empty (use setImmediate for better performance)
            if (this.queue.length > 0) {
                // Use process.nextTick for faster processing
                process.nextTick(() => this.processNext());
            } else {
                this.processing = false;
            }
        }
    }
}

