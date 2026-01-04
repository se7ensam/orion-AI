import axios from 'axios';
import { SecThrottler } from './throttler.js';
import { ENV } from '../config/env.js';

export class SecDownloader {
    private throttler: SecThrottler;

    constructor() {
        this.throttler = new SecThrottler();
    }

    async downloadHtml(url: string): Promise<string> {
        await this.throttler.canRequest();

        // Stub implementation - in real world would use axios with User-Agent
        console.log(`Downloading: ${url}`);

        try {
            const response = await axios.get(url, {
                headers: { 'User-Agent': ENV.USER_AGENT }
            });
            return response.data;
        } catch (error) {
            console.error(`Failed to download ${url}`, error);
            throw error;
        }
    }
}
