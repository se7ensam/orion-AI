#!/usr/bin/env node
/**
 * SEC EDGAR 6-K Filing Downloader Service (TypeScript)
 * 
 * Main entry point for the downloader microservice
 */

import fs from 'fs/promises';
import path from 'path';
import pLimit from 'p-limit';
import cliProgress from 'cli-progress';
import chalk from 'chalk';
import { SEC_RATE_LIMIT, getDataDir, getDownloadRoot, getMetadataDir } from './config.js';
import { RateLimiter } from './rateLimiter.js';
import { getFpiList } from './fpiList.js';
import { getSubmissionJson } from './secApi.js';
import { processFpiEntry } from './filingDownloader.js';
import type { FpiEntry, DownloadOptions } from './types.js';

/**
 * Count total filings to download
 */
async function countTotalFilings(
    fpis: FpiEntry[],
    startDate: Date,
    endDate: Date,
    rateLimiter: RateLimiter
): Promise<number> {
    let total = 0;
    console.log('📊 Counting total filings to download...');
    
    const progressBar = new cliProgress.SingleBar({
        format: 'Scanning: {percentage}%|{bar}| {value}/{total} [{duration}s]',
        barCompleteChar: '\u2588',
        barIncompleteChar: '\u2591',
        hideCursor: true
    });
    
    progressBar.start(fpis.length, 0);
    
    for (let i = 0; i < fpis.length; i++) {
        const fpi = fpis[i];
        const data = await getSubmissionJson(fpi.cik, rateLimiter);
        
        if (data) {
            const recent = data.filings?.recent || {};
            const forms = recent.form || [];
            const dates = recent.filingDate || [];
            
            for (let j = 0; j < forms.length; j++) {
                if (forms[j] === '6-K') {
                    const filingDate = new Date(dates[j]);
                    if (filingDate >= startDate && filingDate <= endDate) {
                        total++;
                    }
                }
            }
        }
        
        progressBar.update(i + 1);
    }
    
    progressBar.stop();
    return total;
}

/**
 * Main download function
 */
export async function download6kFilings(options: DownloadOptions): Promise<void> {
    const {
        startYear = 2009,
        endYear = 2010,
        skipExisting = true,
        downloadDir = null,
        maxWorkers = 10
    } = options;

    const downloadRoot = downloadDir || getDownloadRoot();
    if (downloadDir) {
        process.env.ORION_DATA_DIR = path.dirname(downloadDir);
    }
    
    // Ensure directories exist
    await fs.mkdir(downloadRoot, { recursive: true });
    await fs.mkdir(getMetadataDir(), { recursive: true });
    await fs.mkdir(getDataDir(), { recursive: true });
    
    const startDate = new Date(startYear, 0, 1);
    const endDate = new Date(endYear, 11, 31);
    
    console.log(chalk.blue('═══════════════════════════════════════════════════════════'));
    console.log(chalk.green(`📥 Starting download of 6-K filings from ${startYear} to ${endYear}`));
    console.log(chalk.yellow(`📁 Data directory: ${getDataDir()}`));
    console.log(chalk.yellow(`📁 Download directory: ${downloadRoot}`));
    console.log(chalk.yellow(`⏭️  Skip existing: ${skipExisting}`));
    console.log(chalk.blue('═══════════════════════════════════════════════════════════'));
    console.log();
    
    const fpis = await getFpiList(startYear, endYear);
    console.log(chalk.cyan(`📊 Found ${fpis.length} companies with 6-K filings`));
    
    // Initialize rate limiter
    const rateLimiter = new RateLimiter(SEC_RATE_LIMIT);
    
    // Count total filings
    const totalFilings = await countTotalFilings(fpis, startDate, endDate, rateLimiter);
    console.log(chalk.cyan(`📄 Found ${totalFilings} total filings to download`));
    console.log(chalk.blue('═══════════════════════════════════════════════════════════'));
    console.log();
    
    // Create progress bar
    const progressBar = new cliProgress.SingleBar({
        format: chalk.cyan('Downloading: {percentage}%|{bar}| {value}/{total} [{duration}s<{eta}s, {rate}]'),
        barCompleteChar: '\u2588',
        barIncompleteChar: '\u2591',
        hideCursor: true
    });
    
    progressBar.start(totalFilings, 0);
    
    // Create concurrency limiter
    const limit = pLimit(maxWorkers);
    
    let totalDownloaded = 0;
    const promises = fpis.map(fpi => 
        limit(async () => {
            const count = await processFpiEntry(fpi, startDate, endDate, skipExisting, rateLimiter);
            totalDownloaded += count;
            progressBar.update(totalDownloaded);
            return count;
        })
    );
    
    await Promise.all(promises);
    
    // Flush any remaining metadata
    const { flushMetadata } = await import('./metadataWriter.js');
    await flushMetadata();
    
    progressBar.stop();
    
    console.log();
    console.log(chalk.green('✅ All 6-K filings downloaded.'));
    console.log(chalk.cyan(`📊 Downloaded ${totalDownloaded} filings from ${fpis.length} companies`));
    console.log(chalk.yellow(`📁 Files saved to: ${downloadRoot}`));
    const { getMetadataCsvPath } = await import('./config.js');
    console.log(chalk.yellow(`📋 Metadata saved to: ${getMetadataCsvPath()}`));
}

// CLI interface
if (import.meta.url === `file://${process.argv[1]}`) {
    const args = process.argv.slice(2);

    if (args.length === 0 || args.includes('--help') || args.includes('-h')) {
        console.log(chalk.blue('═══════════════════════════════════════════════════════════'));
        console.log(chalk.green('SEC EDGAR 6-K Filing Downloader Service (TypeScript)'));
        console.log(chalk.blue('═══════════════════════════════════════════════════════════'));
        console.log();
        console.log('Usage:');
        console.log('  node dist/index.js [startYear] [endYear] [options]');
        console.log();
        console.log('Arguments:');
        console.log('  startYear          Starting year (default: 2009)');
        console.log('  endYear            Ending year (default: 2010)');
        console.log();
        console.log('Options:');
        console.log('  --no-skip-existing  Re-download existing files');
        console.log('  --download-dir DIR  Custom download directory');
        console.log('  --max-workers N     Number of parallel workers (default: 10)');
        console.log('  --help, -h          Show this help message');
        console.log();
        console.log('Examples:');
        console.log('  node dist/index.js 2009 2010');
        console.log('  node dist/index.js 2020 2021 --max-workers 20');
        console.log('  node dist/index.js 2009 2010 --no-skip-existing');
        process.exit(0);
    }

    const startYear = parseInt(args[0]) || 2009;
    const endYear = parseInt(args[1]) || 2010;
    const skipExisting = !args.includes('--no-skip-existing');
    const downloadDir = args.includes('--download-dir') 
        ? args[args.indexOf('--download-dir') + 1] 
        : null;
    const maxWorkers = args.includes('--max-workers')
        ? parseInt(args[args.indexOf('--max-workers') + 1])
        : 200; // Default to 200 workers for maximum throughput

    download6kFilings({ startYear, endYear, skipExisting, downloadDir, maxWorkers })
        .catch(error => {
            console.error(chalk.red('❌ Error:'), error);
            process.exit(1);
        });
}

