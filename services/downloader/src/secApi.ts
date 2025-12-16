/**
 * SEC EDGAR API client
 */

import { AxiosError } from 'axios';
import chalk from 'chalk';
import { SUBMISSION_URL } from './config.js';
import { formatCik } from './utils.js';
import { RateLimiter } from './rateLimiter.js';
import { httpClient } from './httpClient.js';
import type { SubmissionData } from './types.js';

/**
 * Get submission JSON for a CIK (single IP version)
 */
export async function getSubmissionJson(
    cik: string,
    rateLimiter: RateLimiter
): Promise<SubmissionData | null> {
    await rateLimiter.wait();
    
    const url = SUBMISSION_URL.replace('{cik}', formatCik(cik));
    try {
        const response = await httpClient.get<SubmissionData>(url);
        return response.data;
    } catch (error) {
        const axiosError = error as AxiosError;
        const status = axiosError.response?.status;
        
        // Retry on 429 (rate limit) or 503 (service unavailable)
        if (status === 429 || status === 503) {
            const waitTime = status === 503 ? 3000 : 5000; // Shorter wait for 503
            const statusMsg = status === 503 ? 'Service unavailable (503)' : 'Rate limited (429)';
            console.log(chalk.yellow(`⚠️  ${statusMsg} for CIK ${cik}, waiting ${waitTime/1000}s...`));
            await new Promise(resolve => setTimeout(resolve, waitTime));
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
    const maxRetries = 3;
    let retryCount = 0;
    
    while (retryCount <= maxRetries) {
        try {
            const response = await httpClient.get<string>(url);
            return response.data;
        } catch (error) {
            const axiosError = error as AxiosError;
            const status = axiosError.response?.status;
            
            // Retry on 503 (service unavailable) or 429 (rate limit)
            if ((status === 503 || status === 429) && retryCount < maxRetries) {
                const backoffTime = Math.min(2000 * Math.pow(2, retryCount), 8000);
                const statusMsg = status === 503 ? 'Service unavailable (503)' : 'Rate limited (429)';
                console.log(chalk.yellow(`⚠️  ${statusMsg} for ${year} Q${qtr}, retrying in ${backoffTime/1000}s...`));
                await new Promise(resolve => setTimeout(resolve, backoffTime));
                retryCount++;
                continue;
            }
            
            // Don't retry on other errors
            if (status === 403) {
                console.log(chalk.red(`❌ Access forbidden (403) for ${year} Q${qtr}. SEC may require proper User-Agent header.`));
            } else {
                console.log(chalk.red(`❌ Could not download index for ${year} Q${qtr}: ${axiosError.message}`));
            }
            return null;
        }
    }
    
    return null;
}

