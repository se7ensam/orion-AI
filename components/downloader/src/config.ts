/**
 * Configuration constants and utilities
 */

import path from 'path';

export const HEADERS = { 'User-Agent': 'sambitsrcm@gmail.com' } as const;
export const SUBMISSION_URL = 'https://data.sec.gov/submissions/CIK{cik}.json';
export const ARCHIVE_BASE = 'https://www.sec.gov/Archives/edgar/data';
export const SEC_RATE_LIMIT = 10; // requests per second (SEC limit)
// Use 9.5 to be safe and avoid 429 errors
export const ACTUAL_RATE_LIMIT = 9.5; // requests per second (slightly under limit for safety)
export const MIN_INTERVAL = 1000 / ACTUAL_RATE_LIMIT; // ~105ms between requests

/**
 * Get the data directory from environment or use default
 */
export function getDataDir(): string {
    return process.env.ORION_DATA_DIR || '../data';
}

/**
 * Get the download root directory for filings
 */
export function getDownloadRoot(): string {
    return path.join(getDataDir(), 'filings');
}

/**
 * Get the metadata directory for SEC company index files
 */
export function getMetadataDir(): string {
    return path.join(getDataDir(), 'metadata');
}

/**
 * Get the path to fpi_list.csv file
 */
export function getFpiListPath(): string {
    return path.join(getDataDir(), 'fpi_list.csv');
}

/**
 * Get the path to fpi_6k_metadata.csv file
 */
export function getMetadataCsvPath(): string {
    return path.join(getDataDir(), 'fpi_6k_metadata.csv');
}

