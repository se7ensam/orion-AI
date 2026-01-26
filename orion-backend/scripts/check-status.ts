import { Pool } from 'pg';
import path from 'path';
import * as dotenv from 'dotenv';

// Load env from the worker service
const workerEnvPath = path.join(process.cwd(), '../services/ingestion-worker/.env');
dotenv.config({ path: workerEnvPath });

const DATABASE_URL = process.env.DATABASE_URL || 'postgres://orion:orion_password@localhost:5432/orion';

async function main() {
    const pool = new Pool({ connectionString: DATABASE_URL });

    try {
        console.log('Checking filing statuses...');
        const res = await pool.query(`
            SELECT status, COUNT(*) as count 
            FROM filings 
            GROUP BY status 
            ORDER BY count DESC
        `);

        console.table(res.rows);

        const totalRes = await pool.query('SELECT COUNT(*) as total FROM filings');
        console.log(`Total filings: ${totalRes.rows[0].total}`);

    } catch (error) {
        console.error('Error querying database:', error);
    } finally {
        await pool.end();
    }
}

main().catch(console.error);
