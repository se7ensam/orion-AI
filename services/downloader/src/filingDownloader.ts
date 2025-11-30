/**
 * Filing download and processing
 */

import fs from 'fs/promises';
import path from 'path';
import { AxiosError } from 'axios';
import * as cheerio from 'cheerio';
import chalk from 'chalk';
import { ARCHIVE_BASE, getDownloadRoot } from './config.js';
import { RateLimiter } from './rateLimiter.js';
import { httpClient } from './httpClient.js';
import { MultiIpClient } from './multiIpClient.js';
import { getMetadataWriter } from './metadataWriter.js';
import type { FilingResult, FilingMetadata, FpiEntry } from './types.js';

/**
 * Extract EX-99 exhibits from filing text
 */
export async function extractExhibitsAll(
    txtPath: string,
    folder: string,
    originalFilename?: string
): Promise<string[]> {
    const text = await fs.readFile(txtPath, 'utf-8');
    const exhibitsSaved: string[] = [];
    const exhibitCounter: Record<string, number> = {};
    
    // Get base filename from txtPath if originalFilename not provided
    const baseFilename = originalFilename || path.basename(txtPath, '.txt');
    
    // Split into <DOCUMENT> blocks
    const docs = text.split(/<DOCUMENT>/);
    
    for (const doc of docs) {
        const typeMatch = doc.match(/<TYPE>(.+)/);
        if (typeMatch) {
            const doctype = typeMatch[1].trim().toUpperCase();
            
            if (doctype.startsWith('EX-99')) {
                const textMatch = doc.match(/<TEXT>(.*)<\/TEXT>/is);
                if (textMatch) {
                    const rawHtml = textMatch[1];
                    const $ = cheerio.load(rawHtml);
                    const cleanText = $.text().trim();
                    
                    // Handle multiple exhibits of same type
                    let exhibitFilename: string;
                    if (doctype in exhibitCounter) {
                        exhibitCounter[doctype]++;
                        exhibitFilename = `${baseFilename}-${doctype}_${exhibitCounter[doctype]}.txt`;
                    } else {
                        exhibitCounter[doctype] = 0;
                        exhibitFilename = `${baseFilename}-${doctype}.txt`;
                    }
                    
                    const exhibitFile = path.join(folder, exhibitFilename);
                    await fs.writeFile(exhibitFile, cleanText, 'utf-8');
                    exhibitsSaved.push(exhibitFile);
                }
            }
        }
    }
    
    return exhibitsSaved;
}

/**
 * Download a single filing (single IP version)
 */
export async function downloadFiling(
    companyName: string,
    cik: string,
    accession: string,
    filingDate: string,
    skipExisting: boolean,
    rateLimiter: RateLimiter
): Promise<FilingResult> {
    return downloadFilingWithClient(companyName, cik, accession, filingDate, skipExisting, httpClient, rateLimiter);
}

/**
 * Download a single filing (multi-IP version)
 */
export async function downloadFilingMultiIp(
    companyName: string,
    cik: string,
    accession: string,
    filingDate: string,
    skipExisting: boolean,
    multiIpClient: MultiIpClient
): Promise<FilingResult> {
    const { ip, client, rateLimiter } = multiIpClient.getNextIpAndClient();
    return downloadFilingWithClient(companyName, cik, accession, filingDate, skipExisting, client, rateLimiter, ip.id, multiIpClient);
}

/**
 * Core download logic (shared between single and multi-IP)
 */
async function downloadFilingWithClient(
    _companyName: string, // Used in metadata, not in file path
    cik: string,
    accession: string,
    filingDate: string,
    skipExisting: boolean,
    client: any,
    rateLimiter: RateLimiter,
    ipId?: string,
    multiIpClient?: MultiIpClient
): Promise<FilingResult> {
    const accNodash = accession.replace(/-/g, '');
    const year = filingDate.substring(0, 4);
    
    // New structure: data/filings/{year}/
    const yearDir = path.join(getDownloadRoot(), year);
    await fs.mkdir(yearDir, { recursive: true });
    
    // Original filename is the accession number
    const originalFilename = accession.replace(/-/g, '');
    const htmlPath = path.join(yearDir, `${originalFilename}.htm`);
    const txtPath = path.join(yearDir, `${originalFilename}.txt`);
    
    // Check if already downloaded
    if (skipExisting) {
        try {
            await fs.access(htmlPath);
            await fs.access(txtPath);
            
            // Check for exhibits in the year directory
            const files = await fs.readdir(yearDir);
            const exhibits = files
                .filter(f => f.startsWith(`${originalFilename}-EX-99`) && f.endsWith('.txt'))
                .map(f => path.join(yearDir, f));
            
            return { htmlPath, txtPath, exhibits };
        } catch {
            // Files don't exist, continue with download
        }
    }
    
    const filingUrl = `${ARCHIVE_BASE}/${parseInt(cik)}/${accNodash}/${accession}-index.html`;
    
    // Retry logic with exponential backoff for 429 errors
    const maxRetries = 3;
    let retryCount = 0;
    
    while (retryCount <= maxRetries) {
        try {
            // Download index HTML
            await rateLimiter.wait();
            if (multiIpClient && ipId) {
                multiIpClient.getIpPool().incrementRequestCount(ipId);
            }
            const htmlResponse = await client.get(filingUrl) as { data: string };
            const $ = cheerio.load(htmlResponse.data);
            
            // Fix relative URLs
            $('link[href^="/"], script[src^="/"], img[src^="/"], a[href^="/"]').each((_, el) => {
                const attr = el.name === 'link' || el.name === 'a' ? 'href' : 'src';
                const url = $(el).attr(attr);
                if (url) {
                    $(el).attr(attr, new URL(url, 'https://www.sec.gov').href);
                }
            });
            
            await fs.writeFile(htmlPath, $.html(), 'utf-8');
            
            // Find Complete submission text file link
            let txtLink: string | null = null;
            $('tr').each((_, row) => {
                const cols = $(row).find('td');
                if (cols.length >= 3) {
                    const text = $(cols[1]).text().trim();
                    if (text.includes('Complete submission text file')) {
                        const link = $(cols[2]).find('a').attr('href');
                        if (link) {
                            txtLink = new URL(link, 'https://www.sec.gov').href;
                            return false; // break
                        }
                    }
                }
                return true; // continue
            });
            
            let exhibits: string[] = [];
            if (txtLink) {
                // Download text file with retry logic for 503 errors
                let txtRetryCount = 0;
                while (txtRetryCount <= maxRetries) {
                    try {
                        await rateLimiter.wait();
                        if (multiIpClient && ipId) {
                            multiIpClient.getIpPool().incrementRequestCount(ipId);
                        }
                        const txtResponse = await client.get(txtLink) as { data: string };
                        await fs.writeFile(txtPath, txtResponse.data, 'utf-8');
                        
                        // Extract exhibits to the same year directory with original filename prefix
                        exhibits = await extractExhibitsAll(txtPath, yearDir, originalFilename);
                        break; // Success, exit retry loop
                    } catch (txtError) {
                        const txtAxiosError = txtError as AxiosError;
                        if ((txtAxiosError.response?.status === 503 || txtAxiosError.response?.status === 429) && txtRetryCount < maxRetries) {
                            const backoffTime = Math.min(2000 * Math.pow(2, txtRetryCount), 8000);
                            await new Promise(resolve => setTimeout(resolve, backoffTime));
                            txtRetryCount++;
                            continue;
                        }
                        throw txtError; // Re-throw if not retryable or max retries reached
                    }
                }
            }
            
            return { htmlPath, txtPath, exhibits };
        } catch (error) {
            const axiosError = error as AxiosError;
            const status = axiosError.response?.status;
            
            // Retry on 429 (rate limit) or 503 (service unavailable)
            if ((status === 429 || status === 503) && retryCount < maxRetries) {
                const backoffTime = Math.min(2000 * Math.pow(2, retryCount), 8000);
                const statusMsg = status === 503 ? 'Service unavailable (503)' : 'Rate limited (429)';
                console.log(chalk.yellow(`⚠️  ${statusMsg} for ${accession}, retrying in ${backoffTime/1000}s... (attempt ${retryCount + 1}/${maxRetries})`));
                await new Promise(resolve => setTimeout(resolve, backoffTime));
                retryCount++;
                continue; // Retry
            }
            
            // Log error and return failure
            if (status !== 429 && status !== 503) {
                console.log(chalk.red(`❌ Failed to download ${accession}: ${axiosError.message}`));
            }
            return { htmlPath: null, txtPath: null, exhibits: [] };
        }
    }
    
    return { htmlPath: null, txtPath: null, exhibits: [] };
}

/**
 * Process a single FPI entry - returns list of filings to download
 */
export async function getFilingsForCompany(
    entry: FpiEntry,
    startDate: Date,
    endDate: Date,
    rateLimiter: RateLimiter
): Promise<Array<{companyName: string; cik: string; accession: string; filingDate: string}>> {
    const cik = entry.cik;
    const companyName = entry.company_name;
    
    const { getSubmissionJson } = await import('./secApi.js');
    const data = await getSubmissionJson(cik, rateLimiter);
    if (!data) {
        return [];
    }
    
    const recent = data.filings?.recent || {};
    const forms = recent.form || [];
    const dates = recent.filingDate || [];
    const accessions = recent.accessionNumber || [];
    
    const filings: Array<{companyName: string; cik: string; accession: string; filingDate: string}> = [];
    
    for (let i = 0; i < forms.length; i++) {
        if (forms[i] !== '6-K') continue;
        
        const filingDate = new Date(dates[i]);
        if (filingDate < startDate || filingDate > endDate) continue;
        
        const accession = accessions[i].replace(/-/g, '');
        const accessionFormatted = `${accession.substring(0, 10)}-${accession.substring(10, 12)}-${accession.substring(12)}`;
        
        filings.push({
            companyName,
            cik,
            accession: accessionFormatted,
            filingDate: dates[i]
        });
    }
    
    return filings;
}

/**
 * Process a single FPI entry (legacy - kept for compatibility)
 */
export async function processFpiEntry(
    entry: FpiEntry,
    startDate: Date,
    endDate: Date,
    skipExisting: boolean,
    rateLimiter: RateLimiter
): Promise<number> {
    const filings = await getFilingsForCompany(entry, startDate, endDate, rateLimiter);
    
    let filingsProcessed = 0;
    
    for (const filing of filings) {
        const result = await downloadFiling(
            filing.companyName,
            filing.cik,
            filing.accession,
            filing.filingDate,
            skipExisting,
            rateLimiter
        );
        
        if (result.htmlPath && result.txtPath) {
            filingsProcessed++;
            
            // Batch metadata writes for better performance
            const metadata: FilingMetadata = {
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
        }
    }
    
    return filingsProcessed;
}

