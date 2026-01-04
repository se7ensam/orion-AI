export class SecThrottler {
    private lastRequestTime: number = 0;
    // SEC allows 10 req/sec, but we'll be conservative and use 8 req/sec (125ms between requests)
    private readonly minIntervalMs: number = 125; // ~8 requests per second (conservative limit)
    private rateLimitBlockedUntil: number = 0; // Timestamp when rate limit block expires

    /**
     * Check if we can make a request, waiting if necessary.
     * Returns true if request can proceed, false if blocked by rate limit.
     */
    async canRequest(): Promise<boolean> {
        const now = Date.now();
        
        // Check if we're still blocked by a previous 429 error
        if (now < this.rateLimitBlockedUntil) {
            const waitTime = this.rateLimitBlockedUntil - now;
            console.log(`⏸️  Rate limited. Waiting ${Math.ceil(waitTime / 1000)}s before retrying...`);
            await new Promise(resolve => setTimeout(resolve, waitTime));
            return true;
        }
        
        // Normal rate limiting
        if (now - this.lastRequestTime >= this.minIntervalMs) {
            this.lastRequestTime = now;
            return true;
        }
        
        // Wait until minimum interval has passed
        const waitTime = this.minIntervalMs - (now - this.lastRequestTime);
        await new Promise(resolve => setTimeout(resolve, waitTime));
        this.lastRequestTime = Date.now();
        return true;
    }

    /**
     * Handle a 429 rate limit error by blocking requests for 10 minutes.
     * SEC's policy: "Your access to SEC.gov will be limited for 10 minutes"
     */
    handleRateLimitError(): void {
        const blockDurationMs = 10 * 60 * 1000; // 10 minutes in milliseconds
        this.rateLimitBlockedUntil = Date.now() + blockDurationMs;
        console.error(`🚫 Rate limit exceeded! Blocked for 10 minutes until ${new Date(this.rateLimitBlockedUntil).toISOString()}`);
    }

    /**
     * Check if we're currently blocked by rate limiting.
     */
    isBlocked(): boolean {
        return Date.now() < this.rateLimitBlockedUntil;
    }
}
