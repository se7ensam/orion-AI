import fs from 'fs-extra';
import path from 'path';
import readline from 'readline';

const INPUT_FILE = path.join(process.cwd(), 'master.idx');
const OUTPUT_FILE = path.join(process.cwd(), 'filings-6k.json');

// Define date range
const START_DATE = '2023-11-01';
const END_DATE = '2023-11-05';

interface RawFiling {
    cik: string;
    name: string;
    formType: string;
    date: string;
    filename: string;
}

async function main() {
    console.log(`Filtering 6-K filings between ${START_DATE} and ${END_DATE}...`);

    if (!fs.existsSync(INPUT_FILE)) {
        console.error('master.idx not found. Run fetch-master-idx.ts first.');
        process.exit(1);
    }

    const fileStream = fs.createReadStream(INPUT_FILE);
    const rl = readline.createInterface({
        input: fileStream,
        crlfDelay: Infinity
    });

    const filings: any[] = [];
    let lineCount = 0;

    for await (const line of rl) {
        lineCount++;
        if (lineCount < 12) continue; // Skip header

        // CIK|Company Name|Form Type|Date Filed|Filename
        const parts = line.split('|');
        if (parts.length < 5) continue;

        const [cik, name, formType, date, filename] = parts;

        if (formType === '6-K' && date >= START_DATE && date <= END_DATE) {
            // Construct Accession Number from filename
            // Filename format: edgar/data/1067491/0001067491-23-000006.txt
            const accessionNumber = path.basename(filename, '.txt');

            filings.push({
                cik,
                accessionNumber,
                ticker: 'UNKNOWN', // Ticker is not in master.idx
                formType,
                date,
                // Correct URL for the text submission
                url: `https://www.sec.gov/Archives/${filename}`
            });

            if (filings.length >= 500) {
                console.log('Reached limit of 500 filings. Stopping.');
                break;
            }
        }
    }

    console.log(`Found ${filings.length} filings.`);
    await fs.writeJson(OUTPUT_FILE, filings, { spaces: 2 });
    console.log(`Wrote to ${OUTPUT_FILE}`);
}

main().catch(console.error);
