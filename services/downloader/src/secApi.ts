/**
 * SEC EDGAR API client
 */

import { AxiosError } from 'axios';
import chalk from 'chalk';
import { HEADERS, SUBMISSION_URL } from './config.js';
import { formatCik } from './utils.js';
import { RateLimiter } from './rateLimiter.js';
import { httpClient } from './httpClient.js';
import type { SubmissionData } from './types.js';

/**
 * Get submission JSON for a CIK
 */
export async function getSubmissionJson(
    cik: string,
    rateLimiter: RateLimiter
): Promise<SubmissionData | null> {
    await rateLimiter.wait();
    
    const url = SUBMISSION_URL.replace('{cik}', formatCik(cik));
    try {
        const response = await httpClient.get<SubmissionData>(url, { 
            headers: HEADERS 
        });
        return response.data;
    } catch (error) {
        const axiosError = error as AxiosError;
        if (axiosError.response?.status === 429) {
            console.log(chalk.yellow(`⚠️  Rate limited for CIK ${cik}, waiting 5 seconds...`));
            await new Promise(resolve => setTimeout(resolve, 5000));
            return getSubmissionJson(cik, rateLimiter);
        }
        if (axiosError.code === 'ECONNABORTED') {
            console.log(chalk.yellow(`⏱️  Timeout fetching submissions for CIK ${cik}`));
        } else {
            console.log(chalk.red(`❌ Error fetching ${cik}: ${axiosError.message}`));
        }
        return null;
    }
}

/**
 * Download company index file
 */
export async function downloadCompanyIdx(
    year: number,
    qtr: number
): Promise<string | null> {
    const url = `https://www.sec.gov/Archives/edgar/full-index/${year}/QTR${qtr}/company.idx`;
    try {
        const response = await httpClient.get<string>(url, { 
            headers: HEADERS 
        });
        return response.data;
    } catch (error) {
        const axiosError = error as AxiosError;
        console.log(chalk.red(`❌ Could not download index for ${year} Q${qtr}: ${axiosError.message}`));
        return null;
    }
}

