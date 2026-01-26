/**
 * Performance metrics collector for monitoring ingestion worker performance.
 * Tracks key metrics without external dependencies for simplicity.
 */

export interface JobMetrics {
    downloadTimeMs: number;
    cleaningTimeMs: number;
    chunkingTimeMs: number;
    storageTimeMs: number;
    totalTimeMs: number;
    chunksCreated: number;
    rawHtmlSize: number;
    cleanTextSize: number;
}

export interface AggregatedMetrics {
    totalJobsProcessed: number;
    successfulJobs: number;
    failedJobs: number;
    rateLimitErrors: number;
    avgProcessingTimeMs: number;
    avgChunksPerJob: number;
    avgDownloadTimeMs: number;
    avgStorageTimeMs: number;
    minProcessingTimeMs: number;
    maxProcessingTimeMs: number;
}

export class MetricsCollector {
    private jobMetrics: JobMetrics[] = [];
    private totalJobs: number = 0;
    private successfulJobs: number = 0;
    private failedJobs: number = 0;
    private rateLimitErrors: number = 0;
    private readonly maxStoredMetrics: number = 1000; // Keep last 1000 jobs in memory

    recordJob(metrics: JobMetrics): void {
        this.totalJobs++;
        this.successfulJobs++;
        
        this.jobMetrics.push(metrics);
        
        // Keep only the last N metrics to prevent memory bloat
        if (this.jobMetrics.length > this.maxStoredMetrics) {
            this.jobMetrics.shift();
        }
    }

    recordFailure(isRateLimit: boolean = false): void {
        this.totalJobs++;
        this.failedJobs++;
        
        if (isRateLimit) {
            this.rateLimitErrors++;
        }
    }

    getAggregatedMetrics(): AggregatedMetrics {
        if (this.jobMetrics.length === 0) {
            return {
                totalJobsProcessed: this.totalJobs,
                successfulJobs: this.successfulJobs,
                failedJobs: this.failedJobs,
                rateLimitErrors: this.rateLimitErrors,
                avgProcessingTimeMs: 0,
                avgChunksPerJob: 0,
                avgDownloadTimeMs: 0,
                avgStorageTimeMs: 0,
                minProcessingTimeMs: 0,
                maxProcessingTimeMs: 0,
            };
        }

        const totalProcessingTime = this.jobMetrics.reduce((sum, m) => sum + m.totalTimeMs, 0);
        const totalChunks = this.jobMetrics.reduce((sum, m) => sum + m.chunksCreated, 0);
        const totalDownloadTime = this.jobMetrics.reduce((sum, m) => sum + m.downloadTimeMs, 0);
        const totalStorageTime = this.jobMetrics.reduce((sum, m) => sum + m.storageTimeMs, 0);
        
        const processingTimes = this.jobMetrics.map(m => m.totalTimeMs);
        const minTime = Math.min(...processingTimes);
        const maxTime = Math.max(...processingTimes);

        return {
            totalJobsProcessed: this.totalJobs,
            successfulJobs: this.successfulJobs,
            failedJobs: this.failedJobs,
            rateLimitErrors: this.rateLimitErrors,
            avgProcessingTimeMs: Math.round(totalProcessingTime / this.jobMetrics.length),
            avgChunksPerJob: Math.round(totalChunks / this.jobMetrics.length),
            avgDownloadTimeMs: Math.round(totalDownloadTime / this.jobMetrics.length),
            avgStorageTimeMs: Math.round(totalStorageTime / this.jobMetrics.length),
            minProcessingTimeMs: minTime,
            maxProcessingTimeMs: maxTime,
        };
    }

    /**
     * Get recent metrics for the last N jobs
     */
    getRecentMetrics(count: number = 10): JobMetrics[] {
        return this.jobMetrics.slice(-count);
    }

    /**
     * Print metrics summary to console
     */
    printSummary(): void {
        const metrics = this.getAggregatedMetrics();
        
        console.log('\n═══════════════════════════════════════');
        console.log('📊 INGESTION WORKER METRICS SUMMARY');
        console.log('═══════════════════════════════════════');
        console.log(`Total Jobs:          ${metrics.totalJobsProcessed}`);
        console.log(`Successful:          ${metrics.successfulJobs} (${this.getSuccessRate()}%)`);
        console.log(`Failed:              ${metrics.failedJobs}`);
        console.log(`Rate Limit Errors:   ${metrics.rateLimitErrors}`);
        console.log('───────────────────────────────────────');
        console.log(`Avg Processing Time: ${metrics.avgProcessingTimeMs}ms`);
        console.log(`Min Processing Time: ${metrics.minProcessingTimeMs}ms`);
        console.log(`Max Processing Time: ${metrics.maxProcessingTimeMs}ms`);
        console.log(`Avg Download Time:   ${metrics.avgDownloadTimeMs}ms`);
        console.log(`Avg Storage Time:    ${metrics.avgStorageTimeMs}ms`);
        console.log(`Avg Chunks/Job:      ${metrics.avgChunksPerJob}`);
        console.log('═══════════════════════════════════════\n');
    }

    private getSuccessRate(): string {
        if (this.totalJobs === 0) return '0.00';
        return ((this.successfulJobs / this.totalJobs) * 100).toFixed(2);
    }

    /**
     * Reset all metrics
     */
    reset(): void {
        this.jobMetrics = [];
        this.totalJobs = 0;
        this.successfulJobs = 0;
        this.failedJobs = 0;
        this.rateLimitErrors = 0;
    }
}

// Singleton instance for application-wide metrics
export const metricsCollector = new MetricsCollector();
