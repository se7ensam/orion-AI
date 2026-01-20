import { Pool } from 'pg';
import { ENV } from '../config/env.js';
import { IngestionJob } from '@orion/shared';

export class IngestionRepository {
    private pool: Pool;

    constructor() {
        // Optimize connection pool for better performance
        this.pool = new Pool({ 
            connectionString: ENV.DATABASE_URL,
            max: 20, // Maximum number of clients in the pool
            idleTimeoutMillis: 30000, // Close idle clients after 30 seconds
            connectionTimeoutMillis: 2000, // Return an error after 2 seconds if connection could not be established
        });
    }

    async saveFiling(job: IngestionJob, rawText: string): Promise<string> {
        const client = await this.pool.connect();
        try {
            // Insert or update filing (using ON CONFLICT for upsert)
            // Only update raw_text and status if they've changed to avoid unnecessary writes
            const result = await client.query(
                `INSERT INTO filings (cik, accession_number, filing_date, form_type, source_url, raw_text, status)
                 VALUES ($1, $2, $3, $4, $5, $6, 'PROCESSING')
                 ON CONFLICT (cik, accession_number) 
                 DO UPDATE SET 
                     raw_text = EXCLUDED.raw_text,
                     status = CASE 
                         WHEN filings.status != 'COMPLETED' THEN EXCLUDED.status 
                         ELSE filings.status 
                     END,
                     updated_at = CASE 
                         WHEN filings.raw_text IS DISTINCT FROM EXCLUDED.raw_text THEN NOW()
                         ELSE filings.updated_at
                     END
                 RETURNING id`,
                [job.cik, job.accessionNumber, job.date, job.formType, job.url, rawText]
            );
            
            return result.rows[0].id;
        } catch (error) {
            console.error(`Error saving filing for ${job.cik} - ${job.accessionNumber}:`, error);
            throw error;
        } finally {
            client.release();
        }
    }

    async saveChunks(filingId: string, chunks: string[]): Promise<void> {
        if (chunks.length === 0) {
            return;
        }
        
        const client = await this.pool.connect();
        try {
            // Delete existing chunks for this filing (in case of re-processing)
            // Use TRUNCATE for better performance if we're replacing all chunks
            await client.query('DELETE FROM filing_chunks WHERE filing_id = $1', [filingId]);
            
            // PostgreSQL has a limit of 65535 parameters per query
            // Process in batches of 10000 chunks to avoid hitting the limit
            const BATCH_SIZE = 10000;
            
            for (let batchStart = 0; batchStart < chunks.length; batchStart += BATCH_SIZE) {
                const batchEnd = Math.min(batchStart + BATCH_SIZE, chunks.length);
                const batchLength = batchEnd - batchStart;
                
                // Pre-allocate arrays with known size for better performance
                const values: any[] = new Array(batchLength * 3);
                const placeholders: string[] = new Array(batchLength);
                
                // Use for loop instead of forEach for better performance
                for (let batchIndex = 0; batchIndex < batchLength; batchIndex++) {
                    const globalIndex = batchStart + batchIndex;
                    const valueIndex = batchIndex * 3;
                    placeholders[batchIndex] = `($${valueIndex + 1}, $${valueIndex + 2}, $${valueIndex + 3})`;
                    values[valueIndex] = filingId;
                    values[valueIndex + 1] = globalIndex;
                    values[valueIndex + 2] = chunks[batchStart + batchIndex];
                }
                
                // Insert batch in a single query
                await client.query(
                    `INSERT INTO filing_chunks (filing_id, chunk_index, content)
                     VALUES ${placeholders.join(', ')}`,
                    values
                );
            }
        } catch (error) {
            console.error(`Error saving ${chunks.length} chunks for filing ${filingId}:`, error);
            throw error;
        } finally {
            client.release();
        }
    }

    async updateStatus(filingId: string, status: string): Promise<void> {
        const client = await this.pool.connect();
        try {
            // Only update if status is actually changing to avoid unnecessary writes
            // Use RETURNING to check if update actually happened
            const result = await client.query(
                `UPDATE filings 
                 SET status = $1, updated_at = NOW() 
                 WHERE id = $2 AND status != $1
                 RETURNING id`,
                [status, filingId]
            );
            
            // Only log if update actually occurred (status changed)
            if (result.rowCount === 0 && status !== 'COMPLETED') {
                // Status didn't change, but log non-COMPLETED status updates for debugging
                console.log(`Status for ${filingId} already ${status}, skipping update`);
            }
        } catch (error) {
            console.error(`Error updating status for ${filingId} to ${status}:`, error);
            throw error;
        } finally {
            client.release();
        }
    }
}
