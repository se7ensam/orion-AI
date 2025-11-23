/**
 * Type definitions for SEC EDGAR Downloader Service
 */

export interface FpiEntry {
    company_name: string;
    cik: string;
}

export interface SubmissionData {
    filings?: {
        recent?: {
            form?: string[];
            filingDate?: string[];
            accessionNumber?: string[];
        };
    };
}

export interface FilingResult {
    htmlPath: string | null;
    txtPath: string | null;
    exhibits: string[];
}

export interface FilingMetadata {
    company_name: string;
    cik: string;
    accession: string;
    filing_date: string;
    html_path: string;
    txt_path: string;
    exhibits_count: number;
    exhibits: string;
}

export interface DownloadOptions {
    startYear: number;
    endYear: number;
    skipExisting?: boolean;
    downloadDir?: string | null;
    maxWorkers?: number;
}

