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
import { ACTUAL_RATE_LIMIT, getDataDir, getDownloadRoot, getMetadataDir } from './config.js';
import { RateLimiter } from './rateLimiter.js';
import { getFpiList } from './fpiList.js';
import { getSubmissionJson, getSubmissionJsonMultiIp } from './secApi.js';
import { createIpPool } from './ipPool.js';
import { MultiIpClient } from './multiIpClient.js';
import type { FpiEntry, DownloadOptions } from './types.js';

/**
 * Count and collect filings (single IP mode)
 */
async function countAndCollectFilings(
    fpis: FpiEntry[],
    startDate: Date,
    endDate: Date,
    rateLimiter: RateLimiter
): Promise<{total: number; allFilings: Array<{companyName: string; cik: string; accession: string; filingDate: string}>}> {
    let total = 0;
    const allFilings: Array<{companyName: string; cik: string; accession: string; filingDate: string}> = [];
    
    console.log('📊 Scanning companies and collecting filing list...');
    
    const progressBar = new cliProgress.SingleBar({
        format: 'Scanning: {percentage}%|{bar}| {value}/{total} [{duration}s, {rate}/s]',
        barCompleteChar: '\u2588',
        barIncompleteChar: '\u2591',
        hideCursor: true
    });
    
    progressBar.start(fpis.length, 0);
    
    // Parallelize (but still rate-limited)
    const countLimit = pLimit(50);
    let processed = 0;
    
    const promises = fpis.map((fpi) => 
        countLimit(async () => {
            const data = await getSubmissionJson(fpi.cik, rateLimiter);
            
            if (data) {
                const recent = data.filings?.recent || {};
                const forms = recent.form || [];
                const dates = recent.filingDate || [];
                const accessions = recent.accessionNumber || [];
                
                for (let j = 0; j < forms.length; j++) {
                    if (forms[j] === '6-K') {
                        const filingDate = new Date(dates[j]);
                        if (filingDate >= startDate && filingDate <= endDate) {
                            total++;
                            
                            // Collect filing details while we're here
                            const accession = accessions[j].replace(/-/g, '');
                            const accessionFormatted = `${accession.substring(0, 10)}-${accession.substring(10, 12)}-${accession.substring(12)}`;
                            
                            allFilings.push({
                                companyName: fpi.company_name,
                                cik: fpi.cik,
                                accession: accessionFormatted,
                                filingDate: dates[j]
                            });
                        }
                    }
                }
            }
            
            processed++;
            progressBar.update(processed);
        })
    );
    
    await Promise.all(promises);
    
    progressBar.stop();
    return { total, allFilings };
}

/**
 * Count and collect filings using multi-IP (optimized)
 */
async function countAndCollectFilingsMultiIp(
    fpis: FpiEntry[],
    startDate: Date,
    endDate: Date,
    multiIpClient: MultiIpClient
): Promise<{total: number; allFilings: Array<{companyName: string; cik: string; accession: string; filingDate: string}>}> {
    let total = 0;
    const allFilings: Array<{companyName: string; cik: string; accession: string; filingDate: string}> = [];
    
    console.log('📊 Scanning companies and collecting filing list...');
    
    const progressBar = new cliProgress.SingleBar({
        format: 'Scanning: {percentage}%|{bar}| {value}/{total} [{duration}s, {rate}/s]',
        barCompleteChar: '\u2588',
        barIncompleteChar: '\u2591',
        hideCursor: true
    });
    
    progressBar.start(fpis.length, 0);
    
    // Parallelize (but still rate-limited per IP)
    const ipCount = multiIpClient.getIpPool().getIpCount();
    const countLimit = pLimit(50 * ipCount); // Scale workers with IP count
    let processed = 0;
    
    const promises = fpis.map((fpi) => 
        countLimit(async () => {
            const data = await getSubmissionJsonMultiIp(fpi.cik, multiIpClient);
            
            if (data) {
                const recent = data.filings?.recent || {};
                const forms = recent.form || [];
                const dates = recent.filingDate || [];
                const accessions = recent.accessionNumber || [];
                
                let count = 0;
                for (let j = 0; j < forms.length; j++) {
                    if (forms[j] === '6-K') {
                        const filingDate = new Date(dates[j]);
                        if (filingDate >= startDate && filingDate <= endDate) {
                            count++;
                            
                            // Collect filing details while we're here
                            const accession = accessions[j].replace(/-/g, '');
                            const accessionFormatted = `${accession.substring(0, 10)}-${accession.substring(10, 12)}-${accession.substring(12)}`;
                            
                            allFilings.push({
                                companyName: fpi.company_name,
                                cik: fpi.cik,
                                accession: accessionFormatted,
                                filingDate: dates[j]
                            });
                        }
                    }
                }
                
                total += count;
            }
            
            processed++;
            progressBar.update(processed);
        })
    );
    
    await Promise.all(promises);
    
    progressBar.stop();
    return { total, allFilings };
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
        maxWorkers = 100,
        useMultiIp = false,  // Default to single IP unless explicitly enabled
        maxFilings = undefined  // No limit by default
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
    
    // Initialize rate limiter or multi-IP client based on option
    let rateLimiter: RateLimiter | null = null;
    let multiIpClient: MultiIpClient | null = null;
    
    if (useMultiIp) {
        // Multi-IP mode: use proxies if configured
        const ipPool = createIpPool();
        const ipCount = ipPool.getIpCount();
        
        if (ipCount > 1) {
            multiIpClient = new MultiIpClient(ipPool);
            const totalRateLimit = ipPool.getTotalRateLimit();
            console.log(chalk.cyan(`🌐 Multi-IP mode enabled - Using ${ipCount} IP address(es)`));
            console.log(chalk.cyan(`⚡ Total rate limit: ${totalRateLimit.toFixed(1)} req/sec (${ipCount}x faster!)`));
        } else {
            console.log(chalk.yellow(`⚠️  Multi-IP requested but IP_PROXIES not set. Using single IP mode.`));
            console.log(chalk.yellow(`💡 Set IP_PROXIES environment variable to enable multi-IP mode.`));
            rateLimiter = new RateLimiter(ACTUAL_RATE_LIMIT);
        }
        console.log();
    } else {
        // Single IP mode (default)
        rateLimiter = new RateLimiter(ACTUAL_RATE_LIMIT);
        console.log(chalk.cyan(`🌐 Using single IP mode - Rate limit: ${ACTUAL_RATE_LIMIT} req/sec`));
        console.log();
    }
    
    // Count and collect filings
    let totalFilings: number;
    let allFilings: Array<{companyName: string; cik: string; accession: string; filingDate: string}>;
    
    if (multiIpClient) {
        // Multi-IP mode
        const result = await countAndCollectFilingsMultiIp(fpis, startDate, endDate, multiIpClient);
        totalFilings = result.total;
        allFilings = result.allFilings;
    } else {
        // Single IP mode
        if (!rateLimiter) {
            rateLimiter = new RateLimiter(ACTUAL_RATE_LIMIT);
        }
        const result = await countAndCollectFilings(fpis, startDate, endDate, rateLimiter);
        totalFilings = result.total;
        allFilings = result.allFilings;
    }
    
    // Apply limit if specified
    let filingsToDownload = allFilings;
    let actualTotal = totalFilings;
    if (maxFilings && maxFilings > 0) {
        filingsToDownload = allFilings.slice(0, maxFilings);
        actualTotal = Math.min(totalFilings, maxFilings);
        console.log(chalk.yellow(`⚠️  Limiting download to first ${maxFilings} filings (for testing)`));
    }
    
    console.log(chalk.cyan(`📄 Found ${totalFilings} total filings, downloading ${actualTotal}`));
    console.log(chalk.blue('═══════════════════════════════════════════════════════════'));
    console.log();
    
    // Create progress bar
    const progressBar = new cliProgress.SingleBar({
        format: chalk.cyan('Downloading: {percentage}%|{bar}| {value}/{total} [{duration}s<{eta}s, {rate}]'),
        barCompleteChar: '\u2588',
        barIncompleteChar: '\u2591',
        hideCursor: true
    });
    
    progressBar.start(actualTotal, 0);
    
    // Now process all filings in parallel (flattened approach)
    const limit = pLimit(maxWorkers);
    let totalDownloaded = 0;
    
    const promises = filingsToDownload.map(filing => 
        limit(async () => {
            const { downloadFiling, downloadFilingMultiIp } = await import('./filingDownloader.js');
            const { getMetadataWriter } = await import('./metadataWriter.js');
            
            let result;
            if (multiIpClient) {
                result = await downloadFilingMultiIp(
                    filing.companyName,
                    filing.cik,
                    filing.accession,
                    filing.filingDate,
                    skipExisting,
                    multiIpClient
                );
            } else {
                if (!rateLimiter) {
                    rateLimiter = new RateLimiter(ACTUAL_RATE_LIMIT);
                }
                result = await downloadFiling(
                    filing.companyName,
                    filing.cik,
                    filing.accession,
                    filing.filingDate,
                    skipExisting,
                    rateLimiter
                );
            }
            
            if (result.htmlPath && result.txtPath) {
                totalDownloaded++;
                
                // Batch metadata writes for better performance
                const metadata = {
                    company_name: filing.companyName,
                    cik: filing.cik,
                    accession: filing.accession,
                    filing_date: filing.filingDate,
                    html_path: result.htmlPath,
                    txt_path: result.txtPath,
                    exhibits_count: result.exhibits.length,
                    exhibits: result.exhibits.join(';')
                };
                
                const writer = getMetadataWriter();
                await writer.add(metadata);
                progressBar.update(totalDownloaded);
            }
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
        console.log('  --max-workers N     Number of parallel workers (default: 100)');
        console.log('  --max-filings N     Maximum number of filings to download (for testing)');
        console.log('  --use-multi-ip      Enable multi-IP parallel processing (requires IP_PROXIES env var)');
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
        : 100; // Default to 100 workers (rate limiter handles throttling)
    const useMultiIp = args.includes('--use-multi-ip') || args.includes('--multi-ip');
    const maxFilings = args.includes('--max-filings')
        ? parseInt(args[args.indexOf('--max-filings') + 1])
        : undefined;

    download6kFilings({ startYear, endYear, skipExisting, downloadDir, maxWorkers, useMultiIp, maxFilings })
        .catch(error => {
            console.error(chalk.red('❌ Error:'), error);
            process.exit(1);
        });
}

