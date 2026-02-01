import fs from 'fs-extra';
import path from 'path';
import readline from 'readline';

const INPUT_FILE = path.join(process.cwd(), 'master.idx');
const OUTPUT_FILE = path.join(process.cwd(), 'filings-6k.json');

// Define date range
const START_DATE = '2023-11-01';
const END_DATE = '2023-11-05';
const MAX_FILINGS = 500; // Limit to prevent memory issues

interface RawFiling {
    cik: string;
    name: string;
    formType: string;
    date: string;
    filename: string;
}

interface IngestionJob {
    cik: string;
    accessionNumber: string;
    ticker: string;
    formType: string;
    date: string;
    url: string;
}

async function main() {
    console.log(`Filtering 6-K filings between ${START_DATE} and ${END_DATE}...`);
    console.log(`Max filings: ${MAX_FILINGS}`);

    if (!fs.existsSync(INPUT_FILE)) {
        console.error('❌ master.idx not found. Run fetch-master-idx.ts first.');
        process.exit(1);
    }

    const fileStats = await fs.stat(INPUT_FILE);
    const fileSizeMB = (fileStats.size / 1024 / 1024).toFixed(2);
    console.log(`Reading ${fileSizeMB}MB index file...`);

    const fileStream = fs.createReadStream(INPUT_FILE);
    const rl = readline.createInterface({
        input: fileStream,
        crlfDelay: Infinity
    });

    const filings: IngestionJob[] = [];
    let lineCount = 0;
    let processedLines = 0;
    const startTime = Date.now();

    for await (const line of rl) {
        lineCount++;
        
        // Skip header lines (first 11 lines are header)
        if (lineCount < 12) continue;

        processedLines++;

        // Show progress every 10000 lines
        if (processedLines % 10000 === 0) {
            process.stdout.write(`\rProcessed: ${processedLines.toLocaleString()} lines, Found: ${filings.length} 6-K filings`);
        }

        // CIK|Company Name|Form Type|Date Filed|Filename
        const parts = line.split('|');
        if (parts.length < 5) continue;

        const [cik, name, formType, date, filename] = parts;

        // Filter for 6-K filings in date range
        if (formType === '6-K' && date >= START_DATE && date <= END_DATE) {
            // Construct Accession Number from filename
            // Filename format: edgar/data/1067491/0001067491-23-000006.txt
            const accessionNumber = path.basename(filename, '.txt');

            filings.push({
                cik: cik.trim(),
                accessionNumber,
                ticker: 'UNKNOWN', // Ticker is not in master.idx
                formType,
                date,
                // Correct URL for the text submission
                url: `https://www.sec.gov/Archives/${filename.trim()}`
            });

            // Stop if we've reached the limit
            if (filings.length >= MAX_FILINGS) {
                console.log(`\n✓ Reached limit of ${MAX_FILINGS} filings. Stopping.`);
                break;
            }
        }
    }

    const duration = Date.now() - startTime;
    const linesPerSec = Math.round(processedLines / (duration / 1000));

    console.log(`\n`);
    console.log(`═══════════════════════════════════════`);
    console.log(`📊 FILTERING SUMMARY`);
    console.log(`═══════════════════════════════════════`);
    console.log(`Total lines processed: ${processedLines.toLocaleString()}`);
    console.log(`6-K filings found:     ${filings.length}`);
    console.log(`Processing time:       ${duration}ms (${linesPerSec.toLocaleString()} lines/sec)`);
    console.log(`Date range:            ${START_DATE} to ${END_DATE}`);
    console.log(`═══════════════════════════════════════`);

    if (filings.length === 0) {
        console.log('⚠️  No filings found matching criteria.');
        process.exit(0);
    }

    console.log(`\nWriting ${filings.length} filings to ${path.basename(OUTPUT_FILE)}...`);
    await fs.writeJson(OUTPUT_FILE, filings, { spaces: 2 });
    console.log(`✓ Successfully wrote ${OUTPUT_FILE}`);
}

main().catch(error => {
    console.error('Error filtering filings:', error);
    process.exit(1);
});
