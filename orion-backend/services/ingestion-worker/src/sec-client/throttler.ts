export class SecThrottler {
    private lastRequestTime: number = 0;
    // SEC allows 10 req/sec, but we'll be conservative and use 8 req/sec (125ms between requests)
    private readonly minIntervalMs: number = 125; // ~8 requests per second (conservative limit)
    private rateLimitBlockedUntil: number = 0; // Timestamp when rate limit block expires
    private requestCount: number = 0; // Track total requests for monitoring
    private blockedCount: number = 0; // Track rate limit blocks

    /**
     * Check if we can make a request, waiting if necessary.
     * Returns true if request can proceed, false if blocked by rate limit.
     */
    async canRequest(): Promise<boolean> {
        const now = Date.now();
        
        // Check if we're still blocked by a previous 429 error
        if (now < this.rateLimitBlockedUntil) {
            const waitTime = this.rateLimitBlockedUntil - now;
            // Exponential backoff for repeated blocks
            const adjustedWait = this.blockedCount > 1 ? waitTime * this.blockedCount : waitTime;
            console.log(`⏸️  Rate limited. Waiting ${Math.ceil(adjustedWait / 1000)}s before retrying...`);
            await new Promise(resolve => setTimeout(resolve, adjustedWait));
            return true;
        }
        
        // Normal rate limiting
        if (now - this.lastRequestTime >= this.minIntervalMs) {
            this.lastRequestTime = now;
            this.requestCount++;
            return true;
        }
        
        // Wait until minimum interval has passed
        const waitTime = this.minIntervalMs - (now - this.lastRequestTime);
        await new Promise(resolve => setTimeout(resolve, waitTime));
        this.lastRequestTime = Date.now();
        this.requestCount++;
        return true;
    }

    /**
     * Handle a 429 rate limit error by blocking requests for 10 minutes.
     * SEC's policy: "Your access to SEC.gov will be limited for 10 minutes"
     */
    handleRateLimitError(): void {
        this.blockedCount++;
        const blockDurationMs = 10 * 60 * 1000; // 10 minutes in milliseconds
        this.rateLimitBlockedUntil = Date.now() + blockDurationMs;
        console.error(
            `🚫 Rate limit exceeded (${this.blockedCount} time${this.blockedCount > 1 ? 's' : ''})! ` +
            `Blocked for 10 minutes until ${new Date(this.rateLimitBlockedUntil).toISOString()}`
        );
    }

    /**
     * Check if we're currently blocked by rate limiting.
     */
    isBlocked(): boolean {
        return Date.now() < this.rateLimitBlockedUntil;
    }

    /**
     * Get throttler statistics for monitoring
     */
    getStats() {
        return {
            totalRequests: this.requestCount,
            blockedCount: this.blockedCount,
            isCurrentlyBlocked: this.isBlocked(),
            blockedUntil: this.isBlocked() ? new Date(this.rateLimitBlockedUntil).toISOString() : null,
            requestsPerSecond: this.requestCount > 0 ? 1000 / this.minIntervalMs : 0,
        };
    }

    /**
     * Reset statistics (useful for testing or monitoring resets)
     */
    resetStats(): void {
        this.requestCount = 0;
        this.blockedCount = 0;
        // Don't reset rate limit block - that should persist
    }
}
