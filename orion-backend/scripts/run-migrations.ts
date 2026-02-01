import { Pool } from 'pg';
import fs from 'fs-extra';
import path from 'path';
import * as dotenv from 'dotenv';

// Load environment
const workerEnvPath = path.join(process.cwd(), '../services/ingestion-worker/.env');
if (fs.existsSync(workerEnvPath)) {
    dotenv.config({ path: workerEnvPath });
}

const DATABASE_URL = process.env.DATABASE_URL || 'postgres://orion:orion_password@localhost:5432/orion';
const MIGRATIONS_DIR = path.join(process.cwd(), '../shared/database/migrations');

interface Migration {
    filename: string;
    filepath: string;
    version: number;
}

/**
 * Get list of migration files sorted by version
 */
async function getMigrations(): Promise<Migration[]> {
    const files = await fs.readdir(MIGRATIONS_DIR);
    
    const migrations = files
        .filter(f => f.endsWith('.sql'))
        .map(f => ({
            filename: f,
            filepath: path.join(MIGRATIONS_DIR, f),
            version: parseInt(f.split('_')[0])
        }))
        .sort((a, b) => a.version - b.version);

    return migrations;
}

/**
 * Create migrations tracking table if it doesn't exist
 */
async function ensureMigrationsTable(pool: Pool): Promise<void> {
    await pool.query(`
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            filename TEXT NOT NULL,
            applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    `);
}

/**
 * Get applied migrations
 */
async function getAppliedMigrations(pool: Pool): Promise<number[]> {
    const result = await pool.query<{ version: number }>(
        'SELECT version FROM schema_migrations ORDER BY version'
    );
    return result.rows.map(r => r.version);
}

async function migrate() {
    console.log('═══════════════════════════════════════');
    console.log('DATABASE MIGRATION TOOL');
    console.log('═══════════════════════════════════════\n');
    
    console.log(`Database: ${DATABASE_URL.replace(/:[^:@]+@/, ':****@')}`);
    console.log(`Migrations directory: ${MIGRATIONS_DIR}\n`);

    const pool = new Pool({ connectionString: DATABASE_URL });

    try {
        // Test connection
        console.log('Testing database connection...');
        await pool.query('SELECT 1');
        console.log('✓ Connected successfully\n');

        // Ensure migrations table exists
        console.log('Checking migrations table...');
        await ensureMigrationsTable(pool);
        console.log('✓ Migrations table ready\n');

        // Get migrations
        const migrations = await getMigrations();
        console.log(`Found ${migrations.length} migration file(s):`);
        migrations.forEach(m => console.log(`  - ${m.filename}`));
        console.log('');

        // Get applied migrations
        const appliedVersions = await getAppliedMigrations(pool);
        console.log(`Applied ${appliedVersions.length} migration(s):`);
        appliedVersions.forEach(v => console.log(`  - Version ${v}`));
        console.log('');

        // Find pending migrations
        const pendingMigrations = migrations.filter(
            m => !appliedVersions.includes(m.version)
        );

        if (pendingMigrations.length === 0) {
            console.log('✓ Database is up to date. No migrations to run.');
            return;
        }

        console.log(`${pendingMigrations.length} pending migration(s) to apply:\n`);

        // Apply each pending migration
        for (const migration of pendingMigrations) {
            console.log(`Applying migration ${migration.version}: ${migration.filename}...`);
            
            const startTime = Date.now();
            const sql = await fs.readFile(migration.filepath, 'utf-8');

            const client = await pool.connect();
            try {
                await client.query('BEGIN');

                // Execute migration SQL
                await client.query(sql);

                // Record migration
                await client.query(
                    'INSERT INTO schema_migrations (version, filename) VALUES ($1, $2)',
                    [migration.version, migration.filename]
                );

                await client.query('COMMIT');

                const duration = Date.now() - startTime;
                console.log(`✓ Applied in ${duration}ms\n`);

            } catch (error) {
                await client.query('ROLLBACK');
                throw error;
            } finally {
                client.release();
            }
        }

        console.log('═══════════════════════════════════════');
        console.log(`✓ All migrations applied successfully!`);
        console.log('═══════════════════════════════════════');

    } catch (error: unknown) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        console.error('\n❌ Migration failed:', errorMessage);
        
        if (errorMessage.includes('ECONNREFUSED')) {
            console.error('\n   Cannot connect to database.');
            console.error('   Make sure PostgreSQL is running and DATABASE_URL is correct.');
        } else if (errorMessage.includes('password authentication failed')) {
            console.error('\n   Authentication failed.');
            console.error('   Check your database credentials in DATABASE_URL.');
        } else if (errorMessage.includes('syntax error')) {
            console.error('\n   SQL syntax error in migration file.');
            console.error('   Check the migration SQL for errors.');
        }
        
        process.exit(1);
    } finally {
        await pool.end();
    }
}

migrate();
