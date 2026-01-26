import { Pool, PoolClient } from 'pg';
import { ENV } from '../config/env.js';
import { IngestionJob } from '@orion/shared';

export class IngestionRepository {
    private pool: Pool;

    constructor(pool?: Pool) {
        // Allow pool injection for better resource management
        if (pool) {
            this.pool = pool;
        } else {
            // Optimize connection pool for better performance
            this.pool = new Pool({ 
                connectionString: ENV.DATABASE_URL,
                max: 20, // Maximum number of clients in the pool
                idleTimeoutMillis: 30000, // Close idle clients after 30 seconds
                connectionTimeoutMillis: 2000, // Return an error after 2 seconds if connection could not be established
            });
        }
    }

    /**
     * Save filing with chunks in a single transaction for data integrity.
     * This ensures either all data is saved or none, preventing orphaned records.
     */
    async saveFilingWithChunks(job: IngestionJob, rawText: string, chunks: string[]): Promise<string> {
        const client = await this.pool.connect();
        try {
            await client.query('BEGIN');
            
            // Insert or update filing (using ON CONFLICT for upsert)
            const result = await client.query<{ id: string }>(
                `INSERT INTO filings (cik, accession_number, filing_date, form_type, source_url, raw_text, status)
                 VALUES ($1, $2, $3, $4, $5, $6, 'PROCESSING')
                 ON CONFLICT (cik, accession_number) 
                 DO UPDATE SET 
                     raw_text = EXCLUDED.raw_text,
                     status = 'PROCESSING',
                     updated_at = NOW()
                 RETURNING id`,
                [job.cik, job.accessionNumber, job.date, job.formType, job.url, rawText]
            );
            
            if (!result.rows[0]?.id) {
                throw new Error('Failed to get filing ID from database');
            }
            
            const filingId = result.rows[0].id;
            
            // Save chunks within same transaction
            if (chunks.length > 0) {
                await this._saveChunksInternal(client, filingId, chunks);
            }
            
            // Update status to COMPLETED
            await client.query(
                'UPDATE filings SET status = $1, updated_at = NOW() WHERE id = $2',
                ['COMPLETED', filingId]
            );
            
            await client.query('COMMIT');
            return filingId;
        } catch (error) {
            await client.query('ROLLBACK');
            console.error(`Error saving filing with chunks for ${job.cik} - ${job.accessionNumber}:`, error);
            throw error;
        } finally {
            client.release();
        }
    }

    /**
     * Internal method to save chunks using an existing client/transaction.
     */
    private async _saveChunksInternal(client: PoolClient, filingId: string, chunks: string[]): Promise<void> {
        // Delete existing chunks for this filing (in case of re-processing)
        await client.query('DELETE FROM filing_chunks WHERE filing_id = $1', [filingId]);
        
        // PostgreSQL has a limit of 65535 parameters per query
        // With 3 params per chunk, we can do ~21,000 chunks per query
        // Use 10,000 as a safe batch size
        const BATCH_SIZE = 10000;
        
        for (let batchStart = 0; batchStart < chunks.length; batchStart += BATCH_SIZE) {
            const batchEnd = Math.min(batchStart + BATCH_SIZE, chunks.length);
            const batchLength = batchEnd - batchStart;
            
            // Pre-allocate arrays with known size for better performance
            const values: (string | number)[] = new Array(batchLength * 3);
            const placeholders: string[] = new Array(batchLength);
            
            // Use for loop instead of forEach for better performance
            for (let batchIndex = 0; batchIndex < batchLength; batchIndex++) {
                const globalIndex = batchStart + batchIndex;
                const valueIndex = batchIndex * 3;
                placeholders[batchIndex] = `($${valueIndex + 1}, $${valueIndex + 2}, $${valueIndex + 3})`;
                values[valueIndex] = filingId;
                values[valueIndex + 1] = globalIndex;
                values[valueIndex + 2] = chunks[globalIndex];
            }
            
            // Insert batch in a single query
            await client.query(
                `INSERT INTO filing_chunks (filing_id, chunk_index, content)
                 VALUES ${placeholders.join(', ')}`,
                values
            );
        }
    }

    /**
     * Gracefully close the connection pool.
     */
    async close(): Promise<void> {
        await this.pool.end();
    }

    /**
     * Get pool statistics for monitoring.
     */
    getPoolStats() {
        return {
            totalCount: this.pool.totalCount,
            idleCount: this.pool.idleCount,
            waitingCount: this.pool.waitingCount,
        };
    }
}
