import { Pool } from 'pg';
import { ENV } from '../config/env.js';
import { IngestionJob } from '@orion/shared';

export class IngestionRepository {
    private pool: Pool;

    constructor() {
        this.pool = new Pool({ connectionString: ENV.DATABASE_URL });
    }

    async saveFiling(job: IngestionJob, rawText: string): Promise<string> {
        console.log(`Saving filing for ${job.cik} - ${job.accessionNumber}`);
        // Stub: Insert into filings table
        return 'filing-uuid-123';
    }

    async saveChunks(filingId: string, chunks: string[]): Promise<void> {
        console.log(`Saving ${chunks.length} chunks for filing ${filingId}`);
        // Stub: Insert into filing_chunks table
    }

    async updateStatus(filingId: string, status: string): Promise<void> {
        console.log(`Updating status of ${filingId} to ${status}`);
    }
}
