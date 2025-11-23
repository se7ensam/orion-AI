/**
 * Parsing utilities for SEC EDGAR data
 */

import type { FpiEntry } from './types.js';

/**
 * Parse company index file to extract FPIs that filed 6-K forms
 */
export function parseIdxFile(idxText: string): FpiEntry[] {
    const fpiDict = new Map<string, FpiEntry>();
    const lines = idxText.split('\n');
    
    // Skip first ~10 lines (header)
    for (let i = 10; i < lines.length; i++) {
        const line = lines[i];
        try {
            const formType = line.substring(62, 74).trim();
            if (formType === '6-K') {
                const companyName = line.substring(0, 62).trim();
                const cik = line.substring(74, 86).trim();
                if (cik && !fpiDict.has(cik)) {
                    fpiDict.set(cik, { company_name: companyName, cik });
                }
            }
        } catch (e) {
            continue;
        }
    }
    
    return Array.from(fpiDict.values());
}

