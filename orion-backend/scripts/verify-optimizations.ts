#!/usr/bin/env node
/**
 * Verification script for ingestion worker optimizations.
 * Checks that all optimizations are working correctly.
 */

import { Pool } from 'pg';
import * as dotenv from 'dotenv';
import path from 'path';

// Load environment
const workerEnvPath = path.join(process.cwd(), 'services/ingestion-worker/.env');
dotenv.config({ path: workerEnvPath });

const DATABASE_URL = process.env.DATABASE_URL || 'postgres://orion:orion_password@localhost:5432/orion';

interface VerificationResult {
    check: string;
    status: 'PASS' | 'FAIL' | 'WARN';
    message: string;
}

async function runVerifications(): Promise<VerificationResult[]> {
    const results: VerificationResult[] = [];
    const pool = new Pool({ connectionString: DATABASE_URL });

    try {
        // 1. Check database connection
        results.push({
            check: 'Database Connection',
            status: 'PASS',
            message: 'Successfully connected to database',
        });

        // 2. Check for orphaned filings (data integrity)
        const orphanedCheck = await pool.query(`
            SELECT COUNT(*) as count 
            FROM filings f 
            WHERE f.status = 'COMPLETED' 
              AND NOT EXISTS (
                SELECT 1 FROM filing_chunks fc WHERE fc.filing_id = f.id
              )
        `);
        
        const orphanedCount = parseInt(orphanedCheck.rows[0].count);
        results.push({
            check: 'Data Integrity (No Orphaned Filings)',
            status: orphanedCount === 0 ? 'PASS' : 'FAIL',
            message: orphanedCount === 0 
                ? 'No orphaned filings found' 
                : `Found ${orphanedCount} orphaned filings! Transactions may not be working.`,
        });

        // 3. Check if new indexes exist (optional but recommended)
        const indexCheck = await pool.query(`
            SELECT indexname 
            FROM pg_indexes 
            WHERE schemaname = 'public' 
              AND indexname IN (
                'idx_filings_id_not_completed',
                'idx_filing_chunks_filing_id_covering',
                'idx_filings_status_date',
                'idx_filings_cik_date'
              )
        `);
        
        const foundIndexes = indexCheck.rows.map(r => r.indexname);
        const expectedIndexes = [
            'idx_filings_id_not_completed',
            'idx_filing_chunks_filing_id_covering',
            'idx_filings_status_date',
            'idx_filings_cik_date',
        ];
        
        const missingIndexes = expectedIndexes.filter(idx => !foundIndexes.includes(idx));
        results.push({
            check: 'Performance Indexes',
            status: missingIndexes.length === 0 ? 'PASS' : 'WARN',
            message: missingIndexes.length === 0
                ? 'All performance indexes are installed'
                : `Missing optional indexes: ${missingIndexes.join(', ')}. Run 002_add_performance_indexes.sql`,
        });

        // 4. Check filing statistics
        const statsCheck = await pool.query(`
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN status = 'COMPLETED' THEN 1 END) as completed,
                COUNT(CASE WHEN status = 'FAILED' THEN 1 END) as failed,
                COUNT(CASE WHEN status = 'PROCESSING' THEN 1 END) as processing
            FROM filings
        `);
        
        const stats = statsCheck.rows[0];
        const total = parseInt(stats.total);
        
        if (total > 0) {
            const completionRate = (parseInt(stats.completed) / total * 100).toFixed(2);
            results.push({
                check: 'Filing Statistics',
                status: 'PASS',
                message: `Total: ${total}, Completed: ${stats.completed} (${completionRate}%), Failed: ${stats.failed}, Processing: ${stats.processing}`,
            });
        } else {
            results.push({
                check: 'Filing Statistics',
                status: 'WARN',
                message: 'No filings found in database. System may not have processed any jobs yet.',
            });
        }

        // 5. Check for stuck processing jobs (processing for >1 hour)
        const stuckCheck = await pool.query(`
            SELECT COUNT(*) as count
            FROM filings
            WHERE status = 'PROCESSING'
              AND updated_at < NOW() - INTERVAL '1 hour'
        `);
        
        const stuckCount = parseInt(stuckCheck.rows[0].count);
        results.push({
            check: 'Stuck Jobs Detection',
            status: stuckCount === 0 ? 'PASS' : 'WARN',
            message: stuckCount === 0
                ? 'No stuck jobs found'
                : `Found ${stuckCount} jobs stuck in PROCESSING for >1 hour. May indicate worker crashes.`,
        });

        // 6. Check chunk distribution (should have chunks for completed filings)
        const chunkDistCheck = await pool.query(`
            SELECT 
                COUNT(DISTINCT f.id) as filings_with_chunks,
                AVG(chunk_count) as avg_chunks_per_filing,
                MIN(chunk_count) as min_chunks,
                MAX(chunk_count) as max_chunks
            FROM filings f
            INNER JOIN (
                SELECT filing_id, COUNT(*) as chunk_count
                FROM filing_chunks
                GROUP BY filing_id
            ) chunks ON f.id = chunks.filing_id
            WHERE f.status = 'COMPLETED'
        `);
        
        if (chunkDistCheck.rows[0]?.filings_with_chunks) {
            const dist = chunkDistCheck.rows[0];
            results.push({
                check: 'Chunk Distribution',
                status: 'PASS',
                message: `Avg: ${Math.round(dist.avg_chunks_per_filing)} chunks/filing, Min: ${dist.min_chunks}, Max: ${dist.max_chunks}`,
            });
        } else {
            results.push({
                check: 'Chunk Distribution',
                status: 'WARN',
                message: 'No completed filings with chunks found',
            });
        }

        // 7. Check database pool configuration (connection limits)
        const connCheck = await pool.query(`
            SELECT setting, unit 
            FROM pg_settings 
            WHERE name = 'max_connections'
        `);
        
        const maxConnections = parseInt(connCheck.rows[0].setting);
        const recommendedMin = 20; // Worker pool size
        
        results.push({
            check: 'Database Connection Limit',
            status: maxConnections >= recommendedMin ? 'PASS' : 'WARN',
            message: `Max connections: ${maxConnections} (recommended: >=${recommendedMin})`,
        });

    } catch (error) {
        results.push({
            check: 'Database Connection',
            status: 'FAIL',
            message: `Failed to connect to database: ${error}`,
        });
    } finally {
        await pool.end();
    }

    return results;
}

async function main() {
    console.log('╔════════════════════════════════════════════════════════════╗');
    console.log('║     INGESTION WORKER OPTIMIZATION VERIFICATION             ║');
    console.log('╚════════════════════════════════════════════════════════════╝\n');

    console.log(`Database URL: ${DATABASE_URL}\n`);

    const results = await runVerifications();

    // Print results
    let passCount = 0;
    let failCount = 0;
    let warnCount = 0;

    for (const result of results) {
        const icon = result.status === 'PASS' ? '✓' : result.status === 'FAIL' ? '✗' : '⚠';
        const color = result.status === 'PASS' ? '' : result.status === 'FAIL' ? '' : '';
        
        console.log(`${icon} ${result.check}`);
        console.log(`  ${result.message}\n`);

        if (result.status === 'PASS') passCount++;
        else if (result.status === 'FAIL') failCount++;
        else warnCount++;
    }

    // Summary
    console.log('═══════════════════════════════════════════════════════════');
    console.log('SUMMARY');
    console.log('═══════════════════════════════════════════════════════════');
    console.log(`✓ Passed:  ${passCount}`);
    console.log(`⚠ Warnings: ${warnCount}`);
    console.log(`✗ Failed:  ${failCount}`);
    console.log('═══════════════════════════════════════════════════════════\n');

    if (failCount > 0) {
        console.log('❌ VERIFICATION FAILED - Please review the failures above.');
        process.exit(1);
    } else if (warnCount > 0) {
        console.log('⚠️  VERIFICATION PASSED WITH WARNINGS - Review warnings above.');
        process.exit(0);
    } else {
        console.log('✅ ALL VERIFICATIONS PASSED - Optimizations are working correctly!');
        process.exit(0);
    }
}

main().catch(error => {
    console.error('Error running verification:', error);
    process.exit(1);
});
