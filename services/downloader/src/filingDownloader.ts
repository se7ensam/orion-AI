/**
 * Filing download and processing
 */

import fs from 'fs/promises';
import path from 'path';
import { AxiosError } from 'axios';
import * as cheerio from 'cheerio';
import chalk from 'chalk';
import { HEADERS, ARCHIVE_BASE, getDownloadRoot } from './config.js';
import { RateLimiter } from './rateLimiter.js';
import { httpClient } from './httpClient.js';
import { getMetadataWriter } from './metadataWriter.js';
import type { FilingResult, FilingMetadata, FpiEntry } from './types.js';

/**
 * Extract EX-99 exhibits from filing text
 */
export async function extractExhibitsAll(
    txtPath: string,
    folder: string
): Promise<string[]> {
    const text = await fs.readFile(txtPath, 'utf-8');
    const exhibitsSaved: string[] = [];
    const exhibitCounter: Record<string, number> = {};
    
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
                        exhibitFilename = `${doctype}_${exhibitCounter[doctype]}.txt`;
                    } else {
                        exhibitCounter[doctype] = 0;
                        exhibitFilename = `${doctype}.txt`;
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
 * Download a single filing
 */
export async function downloadFiling(
    companyName: string,
    cik: string,
    accession: string,
    filingDate: string,
    skipExisting: boolean,
    rateLimiter: RateLimiter
): Promise<FilingResult> {
    const accNodash = accession.replace(/-/g, '');
    const year = filingDate.substring(0, 4);
    
    // Folder per filing
    const folder = path.join(
        getDownloadRoot(),
        companyName,
        `${year}_${companyName}_${cik}`,
        accession
    );
    
    await fs.mkdir(folder, { recursive: true });
    
    const htmlPath = path.join(folder, 'filing.html');
    const txtPath = path.join(folder, `${accession}.txt`);
    
    // Check if already downloaded
    if (skipExisting) {
        try {
            await fs.access(htmlPath);
            await fs.access(txtPath);
            
            // Check for exhibits
            const files = await fs.readdir(folder);
            const exhibits = files
                .filter(f => f.startsWith('EX-99') && f.endsWith('.txt'))
                .map(f => path.join(folder, f));
            
            return { htmlPath, txtPath, exhibits };
        } catch {
            // Files don't exist, continue with download
        }
    }
    
    const filingUrl = `${ARCHIVE_BASE}/${parseInt(cik)}/${accNodash}/${accession}-index.html`;
    
    try {
        // Download index HTML
        await rateLimiter.wait();
        const htmlResponse = await httpClient.get<string>(filingUrl, { 
            headers: HEADERS 
        });
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
            // Download text file
            await rateLimiter.wait();
            const txtResponse = await httpClient.get<string>(txtLink, { 
                headers: HEADERS 
            });
            await fs.writeFile(txtPath, txtResponse.data, 'utf-8');
            
            // Extract exhibits
            exhibits = await extractExhibitsAll(txtPath, folder);
        }
        
        return { htmlPath, txtPath, exhibits };
    } catch (error) {
        const axiosError = error as AxiosError;
        console.log(chalk.red(`❌ Failed to download ${accession}: ${axiosError.message}`));
        return { htmlPath: null, txtPath: null, exhibits: [] };
    }
}

/**
 * Process a single FPI entry
 */
export async function processFpiEntry(
    entry: FpiEntry,
    startDate: Date,
    endDate: Date,
    skipExisting: boolean,
    rateLimiter: RateLimiter
): Promise<number> {
    const cik = entry.cik;
    const companyName = entry.company_name;
    
    const { getSubmissionJson } = await import('./secApi.js');
    const data = await getSubmissionJson(cik, rateLimiter);
    if (!data) {
        return 0;
    }
    
    const recent = data.filings?.recent || {};
    const forms = recent.form || [];
    const dates = recent.filingDate || [];
    const accessions = recent.accessionNumber || [];
    
    let filingsProcessed = 0;
    
    for (let i = 0; i < forms.length; i++) {
        if (forms[i] !== '6-K') continue;
        
        const filingDate = new Date(dates[i]);
        if (filingDate < startDate || filingDate > endDate) continue;
        
        const accession = accessions[i].replace(/-/g, '');
        const accessionFormatted = `${accession.substring(0, 10)}-${accession.substring(10, 12)}-${accession.substring(12)}`;
        
        const result = await downloadFiling(
            companyName,
            cik,
            accessionFormatted,
            dates[i],
            skipExisting,
            rateLimiter
        );
        
        if (result.htmlPath && result.txtPath) {
            filingsProcessed++;
            
            // Batch metadata writes for better performance
            const metadata: FilingMetadata = {
                company_name: companyName,
                cik: cik,
                accession: accessionFormatted,
                filing_date: dates[i],
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

