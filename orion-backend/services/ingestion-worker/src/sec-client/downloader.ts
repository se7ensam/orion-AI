import axios, { AxiosError } from 'axios';
import { SecThrottler } from './throttler.js';
import { ENV } from '../config/env.js';

export class SecDownloader {
    private throttler: SecThrottler;
    private readonly maxRetries: number = 3;
    private readonly baseRetryDelay: number = 5000; // 5 seconds base delay

    constructor() {
        this.throttler = new SecThrottler();
    }

    async downloadHtml(url: string, retryCount: number = 0): Promise<string> {
        // Wait for rate limiter
        await this.throttler.canRequest();

        // Check if we're blocked by rate limiting
        if (this.throttler.isBlocked()) {
            throw new Error('Rate limit block is active. Please wait 10 minutes.');
        }

        // Only log retries to reduce log noise
        if (retryCount > 0) {
            console.log(`Downloading: ${url} (retry ${retryCount}/${this.maxRetries})`);
        }

        try {
            const response = await axios.get(url, {
                headers: { 
                    'User-Agent': ENV.USER_AGENT,
                    'Accept-Encoding': 'gzip, compress, deflate, br'
                },
                timeout: 30000, // 30 second timeout
                validateStatus: (status) => status < 500, // Don't throw on 4xx errors
            });

            // Handle 429 rate limit error
            if (response.status === 429) {
                this.throttler.handleRateLimitError();
                throw new Error(`Rate limit exceeded (429). Blocked for 10 minutes.`);
            }

            // Handle other 4xx errors
            if (response.status >= 400 && response.status < 500) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return response.data;
        } catch (error) {
            const axiosError = error as AxiosError;
            
            // Handle 429 from axios error response
            if (axiosError.response?.status === 429) {
                this.throttler.handleRateLimitError();
                throw new Error(`Rate limit exceeded (429). Blocked for 10 minutes.`);
            }

            // Handle network errors and timeouts with retry
            if (axiosError.code === 'ECONNABORTED' || axiosError.code === 'ETIMEDOUT' || 
                axiosError.code === 'ENOTFOUND' || axiosError.code === 'ECONNRESET') {
                
                if (retryCount < this.maxRetries) {
                    const delay = this.baseRetryDelay * Math.pow(2, retryCount); // Exponential backoff
                    console.log(`⚠️  Network error (${axiosError.code}). Retrying in ${delay/1000}s...`);
                    await new Promise(resolve => setTimeout(resolve, delay));
                    return this.downloadHtml(url, retryCount + 1);
                }
            }

            // Handle 503 Service Unavailable with retry
            if (axiosError.response?.status === 503) {
                if (retryCount < this.maxRetries) {
                    const delay = this.baseRetryDelay * Math.pow(2, retryCount);
                    console.log(`⚠️  Service unavailable (503). Retrying in ${delay/1000}s...`);
                    await new Promise(resolve => setTimeout(resolve, delay));
                    return this.downloadHtml(url, retryCount + 1);
                }
            }

            console.error(`Failed to download ${url}`, error);
            throw error;
        }
    }
}
