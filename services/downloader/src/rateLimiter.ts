/**
 * Thread-safe rate limiter for SEC EDGAR requests
 */

export class RateLimiter {
    private minInterval: number;
    private lastRequestTime: number;

    constructor(maxRate: number = 10) {
        this.minInterval = 1000 / maxRate; // milliseconds
        this.lastRequestTime = 0;
    }

    /**
     * Wait if necessary to respect rate limit
     */
    async wait(): Promise<void> {
        return new Promise((resolve) => {
            const now = Date.now();
            const elapsed = now - this.lastRequestTime;
            
            if (elapsed < this.minInterval) {
                const waitTime = this.minInterval - elapsed;
                setTimeout(() => {
                    this.lastRequestTime = Date.now();
                    resolve();
                }, waitTime);
            } else {
                this.lastRequestTime = Date.now();
                resolve();
            }
        });
    }
}

