/**
 * Optimized HTTP client with connection pooling
 */

import axios, { AxiosInstance } from 'axios';
import http from 'http';
import https from 'https';
import { HEADERS } from './config.js';

// Create a shared axios instance with connection pooling
export const httpClient: AxiosInstance = axios.create({
    timeout: 30000,
    maxRedirects: 5,
    headers: HEADERS, // Include User-Agent header for SEC EDGAR compliance
    // Enable HTTP keep-alive and connection pooling
    httpAgent: new http.Agent({
        keepAlive: true,
        keepAliveMsecs: 1000,
        maxSockets: 500, // Maximum number of sockets per host
        maxFreeSockets: 256, // Maximum number of free sockets
    }),
    httpsAgent: new https.Agent({
        keepAlive: true,
        keepAliveMsecs: 1000,
        maxSockets: 500,
        maxFreeSockets: 256,
    }),
});

