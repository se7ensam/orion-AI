/**
 * Performance profiling utility for identifying bottlenecks.
 * Lightweight profiler that tracks operation timings.
 */

interface ProfileEntry {
    operation: string;
    startTime: number;
    endTime?: number;
    duration?: number;
    metadata?: Record<string, unknown>;
}

export class Profiler {
    private entries: Map<string, ProfileEntry> = new Map();
    private completedEntries: ProfileEntry[] = [];
    private readonly maxEntries: number = 100;

    /**
     * Start timing an operation
     */
    start(operation: string, metadata?: Record<string, unknown>): void {
        this.entries.set(operation, {
            operation,
            startTime: Date.now(),
            metadata,
        });
    }

    /**
     * End timing an operation and record duration
     */
    end(operation: string): number {
        const entry = this.entries.get(operation);
        if (!entry) {
            console.warn(`Profiler: Operation "${operation}" was not started`);
            return 0;
        }

        const endTime = Date.now();
        const duration = endTime - entry.startTime;

        entry.endTime = endTime;
        entry.duration = duration;

        this.completedEntries.push(entry);
        this.entries.delete(operation);

        // Keep only recent entries to prevent memory bloat
        if (this.completedEntries.length > this.maxEntries) {
            this.completedEntries.shift();
        }

        return duration;
    }

    /**
     * Time an async operation automatically
     */
    async time<T>(operation: string, fn: () => Promise<T>, metadata?: Record<string, unknown>): Promise<T> {
        this.start(operation, metadata);
        try {
            const result = await fn();
            this.end(operation);
            return result;
        } catch (error) {
            this.end(operation);
            throw error;
        }
    }

    /**
     * Get statistics for a specific operation
     */
    getStats(operation: string): { count: number; avgDuration: number; minDuration: number; maxDuration: number } | null {
        const entries = this.completedEntries.filter(e => e.operation === operation && e.duration !== undefined);
        
        if (entries.length === 0) {
            return null;
        }

        const durations = entries.map(e => e.duration as number);
        const sum = durations.reduce((a, b) => a + b, 0);

        return {
            count: entries.length,
            avgDuration: Math.round(sum / entries.length),
            minDuration: Math.min(...durations),
            maxDuration: Math.max(...durations),
        };
    }

    /**
     * Get all operation statistics
     */
    getAllStats(): Record<string, ReturnType<typeof this.getStats>> {
        const operations = new Set(this.completedEntries.map(e => e.operation));
        const stats: Record<string, ReturnType<typeof this.getStats>> = {};

        for (const op of operations) {
            stats[op] = this.getStats(op);
        }

        return stats;
    }

    /**
     * Print profiling summary
     */
    printSummary(): void {
        const stats = this.getAllStats();
        const operations = Object.keys(stats);

        if (operations.length === 0) {
            console.log('No profiling data available');
            return;
        }

        console.log('\n═══════════════════════════════════════');
        console.log('⚡ PERFORMANCE PROFILE');
        console.log('═══════════════════════════════════════');

        for (const op of operations) {
            const stat = stats[op];
            if (stat) {
                console.log(`${op}:`);
                console.log(`  Count: ${stat.count}`);
                console.log(`  Avg:   ${stat.avgDuration}ms`);
                console.log(`  Min:   ${stat.minDuration}ms`);
                console.log(`  Max:   ${stat.maxDuration}ms`);
            }
        }

        console.log('═══════════════════════════════════════\n');
    }

    /**
     * Reset profiler
     */
    reset(): void {
        this.entries.clear();
        this.completedEntries = [];
    }

    /**
     * Get current in-progress operations (for debugging)
     */
    getInProgress(): string[] {
        return Array.from(this.entries.keys());
    }
}

// Export singleton for application-wide profiling
export const profiler = new Profiler();
