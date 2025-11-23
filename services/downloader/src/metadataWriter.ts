/**
 * Optimized metadata writer with batching
 */

import fs from 'fs/promises';
import { createObjectCsvWriter } from 'csv-writer';
import { getMetadataCsvPath } from './config.js';
import type { FilingMetadata } from './types.js';

class MetadataWriter {
    private buffer: FilingMetadata[] = [];
    private bufferSize: number = 100; // Batch size
    private csvWriter: any = null;
    private initialized: boolean = false;

    async initialize(): Promise<void> {
        if (this.initialized) return;
        
        const metadataPath = getMetadataCsvPath();
        const fileExists = await fs.access(metadataPath).then(() => true).catch(() => false);
        
        // Get sample metadata to determine headers
        const sample: FilingMetadata = {
            company_name: '',
            cik: '',
            accession: '',
            filing_date: '',
            html_path: '',
            txt_path: '',
            exhibits_count: 0,
            exhibits: ''
        };
        
        this.csvWriter = createObjectCsvWriter({
            path: metadataPath,
            header: Object.keys(sample).map(key => ({ id: key, title: key })),
            append: fileExists
        });
        
        this.initialized = true;
    }

    async add(metadata: FilingMetadata): Promise<void> {
        this.buffer.push(metadata);
        
        if (this.buffer.length >= this.bufferSize) {
            await this.flush();
        }
    }

    async flush(): Promise<void> {
        if (this.buffer.length === 0) return;
        
        if (!this.initialized) {
            await this.initialize();
        }
        
        await this.csvWriter.writeRecords(this.buffer);
        this.buffer = [];
    }
}

// Singleton instance
let metadataWriter: MetadataWriter | null = null;

export function getMetadataWriter(): MetadataWriter {
    if (!metadataWriter) {
        metadataWriter = new MetadataWriter();
    }
    return metadataWriter;
}

export async function flushMetadata(): Promise<void> {
    if (metadataWriter) {
        await metadataWriter.flush();
    }
}

