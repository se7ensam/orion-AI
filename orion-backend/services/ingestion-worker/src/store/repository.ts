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
        
        const client = await this.pool.connect();
        try {
            // Insert or update filing (using ON CONFLICT for upsert)
            const result = await client.query(
                `INSERT INTO filings (cik, accession_number, filing_date, form_type, source_url, raw_text, status)
                 VALUES ($1, $2, $3, $4, $5, $6, 'PROCESSING')
                 ON CONFLICT (cik, accession_number) 
                 DO UPDATE SET 
                     raw_text = EXCLUDED.raw_text,
                     status = EXCLUDED.status,
                     updated_at = NOW()
                 RETURNING id`,
                [job.cik, job.accessionNumber, job.date, job.formType, job.url, rawText]
            );
            
            const filingId = result.rows[0].id;
            console.log(`Saved filing with ID: ${filingId}`);
            return filingId;
        } catch (error) {
            console.error('Error saving filing:', error);
            throw error;
        } finally {
            client.release();
        }
    }

    async saveChunks(filingId: string, chunks: string[]): Promise<void> {
        console.log(`Saving ${chunks.length} chunks for filing ${filingId}`);
        
        const client = await this.pool.connect();
        try {
            // Delete existing chunks for this filing (in case of re-processing)
            await client.query('DELETE FROM filing_chunks WHERE filing_id = $1', [filingId]);
            
            // Insert chunks in a transaction
            await client.query('BEGIN');
            
            try {
                for (let i = 0; i < chunks.length; i++) {
                    await client.query(
                        `INSERT INTO filing_chunks (filing_id, chunk_index, content)
                         VALUES ($1, $2, $3)`,
                        [filingId, i, chunks[i]]
                    );
                }
                
                await client.query('COMMIT');
                console.log(`Successfully saved ${chunks.length} chunks for filing ${filingId}`);
            } catch (error) {
                await client.query('ROLLBACK');
                throw error;
            }
        } catch (error) {
            console.error('Error saving chunks:', error);
            throw error;
        } finally {
            client.release();
        }
    }

    async updateStatus(filingId: string, status: string): Promise<void> {
        console.log(`Updating status of ${filingId} to ${status}`);
        
        const client = await this.pool.connect();
        try {
            await client.query(
                `UPDATE filings 
                 SET status = $1, updated_at = NOW() 
                 WHERE id = $2`,
                [status, filingId]
            );
        } catch (error) {
            console.error('Error updating status:', error);
            throw error;
        } finally {
            client.release();
        }
    }
}
