import axios from 'axios';
import fs from 'fs-extra';
import path from 'path';

// For this phase, we'll hardcode to Q4 2023 for reliable data
const YEAR = '2023';
const QTR = 'QTR4';
const MASTER_IDX_URL = `https://www.sec.gov/Archives/edgar/full-index/${YEAR}/${QTR}/master.idx`;
const OUTPUT_FILE = path.join(process.cwd(), 'master.idx');
const TIMEOUT_MS = 120000; // 2 minutes timeout for large file
const MAX_RETRIES = 3;

async function downloadWithRetry(retryCount: number = 0): Promise<void> {
    try {
        console.log(`Downloading master.idx for ${YEAR} ${QTR}...`);
        console.log(`URL: ${MASTER_IDX_URL}`);
        
        if (retryCount > 0) {
            console.log(`Retry attempt ${retryCount}/${MAX_RETRIES}...`);
        }

        const response = await axios.get(MASTER_IDX_URL, {
            responseType: 'stream',
            timeout: TIMEOUT_MS,
            headers: {
                'User-Agent': 'OrionData/1.0 (contact@example.com)',
                'Accept-Encoding': 'gzip, deflate'
            },
            // Track download progress
            onDownloadProgress: (progressEvent) => {
                if (progressEvent.total) {
                    const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
                    const downloadedMB = (progressEvent.loaded / 1024 / 1024).toFixed(2);
                    const totalMB = (progressEvent.total / 1024 / 1024).toFixed(2);
                    process.stdout.write(`\rDownloading: ${percentCompleted}% (${downloadedMB}/${totalMB} MB)`);
                } else {
                    const downloadedMB = (progressEvent.loaded / 1024 / 1024).toFixed(2);
                    process.stdout.write(`\rDownloading: ${downloadedMB} MB`);
                }
            }
        });

        // Ensure output directory exists
        await fs.ensureDir(path.dirname(OUTPUT_FILE));

        const writer = fs.createWriteStream(OUTPUT_FILE);
        response.data.pipe(writer);

        await new Promise<void>((resolve, reject) => {
            writer.on('finish', () => resolve());
            writer.on('error', reject);
        });

        console.log('\n');

        // Verify file was written
        const stats = await fs.stat(OUTPUT_FILE);
        const sizeMB = (stats.size / 1024 / 1024).toFixed(2);
        
        console.log(`✓ Download complete!`);
        console.log(`  File: ${OUTPUT_FILE}`);
        console.log(`  Size: ${sizeMB} MB`);
        console.log(`  Lines: Counting...`);

        // Count lines for verification
        const content = await fs.readFile(OUTPUT_FILE, 'utf-8');
        const lineCount = content.split('\n').length;
        console.log(`  Lines: ${lineCount.toLocaleString()}`);

    } catch (error: unknown) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        
        // Handle network errors with retry
        if (axios.isAxiosError(error)) {
            if (error.code === 'ECONNABORTED' || error.code === 'ETIMEDOUT') {
                console.error(`\n⚠️  Timeout error: ${errorMessage}`);
            } else if (error.response?.status === 429) {
                console.error(`\n⚠️  Rate limited by SEC. Please wait and try again later.`);
            } else if (error.response?.status && error.response.status >= 500) {
                console.error(`\n⚠️  Server error (${error.response.status}): ${errorMessage}`);
            } else {
                console.error(`\n❌ Network error: ${errorMessage}`);
            }

            // Retry logic
            if (retryCount < MAX_RETRIES) {
                const delaySeconds = Math.pow(2, retryCount) * 5; // Exponential backoff: 5s, 10s, 20s
                console.log(`Retrying in ${delaySeconds} seconds...`);
                await new Promise(resolve => setTimeout(resolve, delaySeconds * 1000));
                return downloadWithRetry(retryCount + 1);
            }
        } else {
            console.error(`\n❌ Failed to download master.idx: ${errorMessage}`);
        }

        // Clean up partial file if exists
        if (await fs.pathExists(OUTPUT_FILE)) {
            await fs.remove(OUTPUT_FILE);
        }

        console.error(`\n❌ Download failed after ${retryCount + 1} attempts.`);
        process.exit(1);
    }
}

async function main() {
    // Check if file already exists
    if (await fs.pathExists(OUTPUT_FILE)) {
        const stats = await fs.stat(OUTPUT_FILE);
        const sizeMB = (stats.size / 1024 / 1024).toFixed(2);
        const ageHours = ((Date.now() - stats.mtimeMs) / (1000 * 60 * 60)).toFixed(1);
        
        console.log(`ℹ️  Existing master.idx found:`);
        console.log(`   Size: ${sizeMB} MB`);
        console.log(`   Age: ${ageHours} hours old`);
        console.log(`   Overwriting...`);
    }

    await downloadWithRetry();
}

main().catch(error => {
    console.error('Unexpected error:', error);
    process.exit(1);
});
