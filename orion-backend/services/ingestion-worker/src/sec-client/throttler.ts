export class SecThrottler {
    private lastRequestTime: number = 0;
    private readonly minIntervalMs: number = 200; // 5 requests per second (Safer limit)

    async canRequest(): Promise<boolean> {
        const now = Date.now();
        if (now - this.lastRequestTime >= this.minIntervalMs) {
            this.lastRequestTime = now;
            return true;
        }
        // Simple wait implementation
        const waitTime = this.minIntervalMs - (now - this.lastRequestTime);
        await new Promise(resolve => setTimeout(resolve, waitTime));
        this.lastRequestTime = Date.now();
        return true;
    }
}
