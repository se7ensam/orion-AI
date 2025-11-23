/**
 * FPI (Foreign Private Issuer) list management
 */

import fs from 'fs/promises';
import chalk from 'chalk';
import { createObjectCsvWriter } from 'csv-writer';
import { getDataDir, getFpiListPath, getMetadataDir } from './config.js';
import { downloadCompanyIdx } from './secApi.js';
import { parseIdxFile } from './parser.js';
import type { FpiEntry } from './types.js';

/**
 * Get list of Foreign Private Issuers that filed 6-K forms
 */
export async function getFpiList(
    startYear: number,
    endYear: number
): Promise<FpiEntry[]> {
    const allFpis = new Map<string, FpiEntry>();
    
    for (let year = startYear; year <= endYear; year++) {
        for (let qtr = 1; qtr <= 4; qtr++) {
            console.log(`Checking ${year} Q${qtr}...`);
            const idxText = await downloadCompanyIdx(year, qtr);
            if (idxText) {
                // Save index file
                const metadataDir = getMetadataDir();
                await fs.mkdir(metadataDir, { recursive: true });
                const filePath = `${metadataDir}/${year}_Q${qtr}_company.idx`;
                await fs.writeFile(filePath, idxText, 'utf-8');
                
                const fpis = parseIdxFile(idxText);
                fpis.forEach(fpi => allFpis.set(fpi.cik, fpi));
            }
        }
    }
    
    const fpiList = Array.from(allFpis.values());
    
    // Save to CSV
    const dataDir = getDataDir();
    await fs.mkdir(dataDir, { recursive: true });
    
    const fpiListPath = getFpiListPath();
    const csvWriter = createObjectCsvWriter({
        path: fpiListPath,
        header: [
            { id: 'company_name', title: 'company_name' },
            { id: 'cik', title: 'cik' }
        ]
    });
    
    await csvWriter.writeRecords(fpiList);
    console.log(chalk.green(`✅ Saved ${fpiList.length} FPIs to ${fpiListPath}`));
    
    return fpiList;
}

