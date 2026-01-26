import { Pool } from 'pg';
import fs from 'fs-extra';
import path from 'path';
import * as dotenv from 'dotenv';

// Load env from the worker service for consistency, or default
const workerEnvPath = path.join(process.cwd(), '../services/ingestion-worker/.env');
dotenv.config({ path: workerEnvPath });

const DATABASE_URL = process.env.DATABASE_URL || 'postgres://orion:orion_password@localhost:5432/orion';

async function migrate() {
    console.log('Running migrations...');
    console.log(`Connecting to ${DATABASE_URL.split('@')[1]}`); // Mask auth info

    const pool = new Pool({ connectionString: DATABASE_URL });

    try {
        // Read the SQL file
        const sqlPath = path.join(process.cwd(), '../shared/database/migrations/001_init.sql');
        const sql = await fs.readFile(sqlPath, 'utf-8');

        console.log(`Executing ${path.basename(sqlPath)}...`);
        await pool.query(sql);

        console.log('Migration completed successfully.');
    } catch (error) {
        console.error('Migration failed:', error);
        process.exit(1);
    } finally {
        await pool.end();
    }
}

migrate();
