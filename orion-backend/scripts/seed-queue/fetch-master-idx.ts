import axios from 'axios';
import fs from 'fs-extra';
import path from 'path';

// For this phase, we'll hardcode to Q4 2023 for reliable data
const YEAR = '2023';
const QTR = 'QTR4';
const MASTER_IDX_URL = `https://www.sec.gov/Archives/edgar/full-index/${YEAR}/${QTR}/master.idx`;
const OUTPUT_FILE = path.join(process.cwd(), 'master.idx');

async function main() {
    console.log(`Downloading master.idx for ${YEAR} ${QTR}...`);
    console.log(`URL: ${MASTER_IDX_URL}`);

    try {
        const response = await axios.get(MASTER_IDX_URL, {
            responseType: 'stream',
            headers: {
                'User-Agent': 'OrionData/1.0 (contact@example.com)'
            }
        });

        const writer = fs.createWriteStream(OUTPUT_FILE);
        response.data.pipe(writer);

        await new Promise((resolve, reject) => {
            writer.on('finish', () => resolve(undefined));
            writer.on('error', reject);
        });

        console.log('Download complete.');
    } catch (error) {
        console.error('Failed to download master.idx:', error);
        process.exit(1);
    }
}

main().catch(console.error);
