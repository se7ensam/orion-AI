import { Pool } from 'pg';
import path from 'path';
import * as dotenv from 'dotenv';
import fs from 'fs-extra';

// Load environment
const workerEnvPath = path.join(process.cwd(), '../services/ingestion-worker/.env');
if (fs.existsSync(workerEnvPath)) {
    dotenv.config({ path: workerEnvPath });
}

const DATABASE_URL = process.env.DATABASE_URL || 'postgres://orion:orion_password@localhost:5432/orion';

async function main() {
    console.log('═══════════════════════════════════════');
    console.log('FILING STATUS REPORT');
    console.log('═══════════════════════════════════════\n');

    const pool = new Pool({ connectionString: DATABASE_URL });

    try {
        // Test connection
        await pool.query('SELECT 1');

        // 1. Status breakdown
        console.log('Status Breakdown:');
        console.log('─────────────────────────────────────');
        const statusRes = await pool.query(`
            SELECT 
                status, 
                COUNT(*) as count,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
            FROM filings 
            GROUP BY status 
            ORDER BY count DESC
        `);

        if (statusRes.rows.length > 0) {
            statusRes.rows.forEach(row => {
                console.log(`  ${row.status.padEnd(12)} ${String(row.count).padStart(6)} (${row.percentage}%)`);
            });
        } else {
            console.log('  No filings found');
        }

        // 2. Total count
        const totalRes = await pool.query('SELECT COUNT(*) as total FROM filings');
        const total = parseInt(totalRes.rows[0].total);
        console.log(`─────────────────────────────────────`);
        console.log(`  Total:       ${total.toLocaleString()}`);
        console.log('');

        // 3. Recent activity
        if (total > 0) {
            console.log('Recent Activity (last 10 filings):');
            console.log('─────────────────────────────────────');
            const recentRes = await pool.query(`
                SELECT 
                    cik, 
                    form_type, 
                    filing_date,
                    status,
                    TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI') as created
                FROM filings 
                ORDER BY created_at DESC 
                LIMIT 10
            `);

            recentRes.rows.forEach(row => {
                console.log(`  CIK ${row.cik} | ${row.form_type} | ${row.filing_date} | ${row.status} | ${row.created}`);
            });
            console.log('');

            // 4. Chunk statistics
            console.log('Chunk Statistics:');
            console.log('─────────────────────────────────────');
            const chunkStats = await pool.query(`
                SELECT 
                    COUNT(DISTINCT fc.filing_id) as filings_with_chunks,
                    COUNT(*) as total_chunks,
                    ROUND(AVG(chunk_count), 0) as avg_chunks,
                    MIN(chunk_count) as min_chunks,
                    MAX(chunk_count) as max_chunks
                FROM filing_chunks fc
                INNER JOIN (
                    SELECT filing_id, COUNT(*) as chunk_count
                    FROM filing_chunks
                    GROUP BY filing_id
                ) counts ON fc.filing_id = counts.filing_id
            `);

            if (chunkStats.rows[0].filings_with_chunks > 0) {
                const stats = chunkStats.rows[0];
                console.log(`  Filings with chunks: ${parseInt(stats.filings_with_chunks).toLocaleString()}`);
                console.log(`  Total chunks:        ${parseInt(stats.total_chunks).toLocaleString()}`);
                console.log(`  Avg chunks/filing:   ${stats.avg_chunks}`);
                console.log(`  Range:               ${stats.min_chunks} - ${stats.max_chunks}`);
            } else {
                console.log('  No chunks found');
            }
            console.log('');

            // 5. Stuck jobs detection
            console.log('Health Check:');
            console.log('─────────────────────────────────────');
            const stuckRes = await pool.query(`
                SELECT COUNT(*) as count
                FROM filings
                WHERE status = 'PROCESSING'
                  AND updated_at < NOW() - INTERVAL '1 hour'
            `);

            const stuckCount = parseInt(stuckRes.rows[0].count);
            if (stuckCount > 0) {
                console.log(`  ⚠️  ${stuckCount} job(s) stuck in PROCESSING for >1 hour`);
            } else {
                console.log(`  ✓ No stuck jobs detected`);
            }

            // 6. Data integrity check
            const orphanedRes = await pool.query(`
                SELECT COUNT(*) as count
                FROM filings f
                WHERE f.status = 'COMPLETED'
                  AND NOT EXISTS (
                    SELECT 1 FROM filing_chunks fc WHERE fc.filing_id = f.id
                  )
            `);

            const orphanedCount = parseInt(orphanedRes.rows[0].count);
            if (orphanedCount > 0) {
                console.log(`  ⚠️  ${orphanedCount} completed filing(s) without chunks`);
            } else {
                console.log(`  ✓ No orphaned filings (data integrity OK)`);
            }
            console.log('');

            // 7. Date range
            console.log('Date Range:');
            console.log('─────────────────────────────────────');
            const dateRange = await pool.query(`
                SELECT 
                    MIN(filing_date) as earliest,
                    MAX(filing_date) as latest
                FROM filings
            `);

            if (dateRange.rows[0].earliest) {
                console.log(`  Earliest: ${dateRange.rows[0].earliest}`);
                console.log(`  Latest:   ${dateRange.rows[0].latest}`);
            }
        }

        console.log('═══════════════════════════════════════');

    } catch (error: unknown) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        console.error('\n❌ Error querying database:', errorMessage);
        
        if (errorMessage.includes('ECONNREFUSED')) {
            console.error('\n   Cannot connect to database.');
            console.error('   Make sure PostgreSQL is running.');
        } else if (errorMessage.includes('relation') && errorMessage.includes('does not exist')) {
            console.error('\n   Tables do not exist.');
            console.error('   Run migrations first: npm run migrations:run');
        }
        
        process.exit(1);
    } finally {
        await pool.end();
    }
}

main().catch(error => {
    console.error('Unexpected error:', error);
    process.exit(1);
});
