/**
 * Multi-IP HTTP Client - Distributes requests across multiple IPs
 */

import axios, { AxiosInstance } from 'axios';
import http from 'http';
import https from 'https';
import { HttpsProxyAgent } from 'https-proxy-agent';
import { HttpProxyAgent } from 'http-proxy-agent';
import { IpPool, IpConfig } from './ipPool.js';
import { HEADERS } from './config.js';

export class MultiIpClient {
    private ipPool: IpPool;
    private clients: Map<string, AxiosInstance>;

    constructor(ipPool: IpPool) {
        this.ipPool = ipPool;
        this.clients = new Map();
        
        // Create HTTP client for each IP
        for (const ip of ipPool.getAllIps()) {
            this.clients.set(ip.id, this.createClientForIp(ip));
        }
    }

    /**
     * Create HTTP client for a specific IP/proxy
     */
    private createClientForIp(ip: IpConfig): AxiosInstance {
        let httpAgent: http.Agent | undefined;
        let httpsAgent: https.Agent | undefined;

        // Configure proxy if provided
        if (ip.proxy) {
            const proxyUrl = ip.proxy.auth
                ? `http://${ip.proxy.auth.username}:${ip.proxy.auth.password}@${ip.proxy.host}:${ip.proxy.port}`
                : `http://${ip.proxy.host}:${ip.proxy.port}`;
            
            httpAgent = new HttpProxyAgent(proxyUrl) as any;
            httpsAgent = new HttpsProxyAgent(proxyUrl) as any;
        } else {
            // Direct connection with connection pooling
            httpAgent = new http.Agent({
                keepAlive: true,
                keepAliveMsecs: 1000,
                maxSockets: 500,
                maxFreeSockets: 256,
                localAddress: ip.localAddress,
            });
            
            httpsAgent = new https.Agent({
                keepAlive: true,
                keepAliveMsecs: 1000,
                maxSockets: 500,
                maxFreeSockets: 256,
                localAddress: ip.localAddress,
            });
        }

        return axios.create({
            timeout: 30000,
            maxRedirects: 5,
            httpAgent,
            httpsAgent,
            headers: HEADERS,
        });
    }

    /**
     * Get a client for a specific IP
     */
    getClient(ipId: string): AxiosInstance {
        const client = this.clients.get(ipId);
        if (!client) {
            throw new Error(`Client not found for IP: ${ipId}`);
        }
        return client;
    }

    /**
     * Get next available IP and its client
     */
    getNextIpAndClient(): { ip: IpConfig; client: AxiosInstance; rateLimiter: any } {
        const ip = this.ipPool.getNextIp();
        const client = this.getClient(ip.id);
        const rateLimiter = this.ipPool.getRateLimiter(ip.id);
        
        return { ip, client, rateLimiter };
    }

    /**
     * Get IP pool
     */
    getIpPool(): IpPool {
        return this.ipPool;
    }
}

