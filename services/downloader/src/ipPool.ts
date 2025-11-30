/**
 * IP Pool Manager - Manages multiple IP addresses/proxies for parallel processing
 */

import { RateLimiter } from './rateLimiter.js';
import { ACTUAL_RATE_LIMIT } from './config.js';

export interface IpConfig {
    id: string;
    proxy?: {
        host: string;
        port: number;
        auth?: {
            username: string;
            password: string;
        };
    };
    // For direct IP binding (if available)
    localAddress?: string;
}

export class IpPool {
    private ips: IpConfig[];
    private rateLimiters: Map<string, RateLimiter>;
    private currentIndex: number;
    private requestCounts: Map<string, number>;

    constructor(ips: IpConfig[]) {
        if (ips.length === 0) {
            throw new Error('IP pool must have at least one IP');
        }
        
        this.ips = ips;
        this.rateLimiters = new Map();
        this.requestCounts = new Map();
        this.currentIndex = 0;
        
        // Create rate limiter for each IP
        for (const ip of ips) {
            this.rateLimiters.set(ip.id, new RateLimiter(ACTUAL_RATE_LIMIT));
            this.requestCounts.set(ip.id, 0);
        }
    }

    /**
     * Get the next available IP (round-robin)
     */
    getNextIp(): IpConfig {
        const ip = this.ips[this.currentIndex];
        this.currentIndex = (this.currentIndex + 1) % this.ips.length;
        return ip;
    }

    /**
     * Get rate limiter for a specific IP
     */
    getRateLimiter(ipId: string): RateLimiter {
        const limiter = this.rateLimiters.get(ipId);
        if (!limiter) {
            throw new Error(`Rate limiter not found for IP: ${ipId}`);
        }
        return limiter;
    }

    /**
     * Get all IPs
     */
    getAllIps(): IpConfig[] {
        return [...this.ips];
    }

    /**
     * Get IP count
     */
    getIpCount(): number {
        return this.ips.length;
    }

    /**
     * Get total rate limit (all IPs combined)
     */
    getTotalRateLimit(): number {
        return ACTUAL_RATE_LIMIT * this.ips.length;
    }

    /**
     * Increment request count for an IP
     */
    incrementRequestCount(ipId: string): void {
        const count = this.requestCounts.get(ipId) || 0;
        this.requestCounts.set(ipId, count + 1);
    }

    /**
     * Get request statistics
     */
    getStats(): Map<string, number> {
        return new Map(this.requestCounts);
    }
}

/**
 * Create IP pool from environment variables or default to single IP
 */
export function createIpPool(): IpPool {
    const ipConfigs: IpConfig[] = [];
    
    // Check for IP_PROXIES environment variable
    // Format: "host1:port1:user1:pass1,host2:port2:user2:pass2" or "host1:port1,host2:port2"
    const proxiesEnv = process.env.IP_PROXIES;
    
            if (proxiesEnv) {
        const proxyStrings = proxiesEnv.split(',').map(s => s.trim());
        
        for (let i = 0; i < proxyStrings.length; i++) {
            const parts = proxyStrings[i].split(':');
            
            if (parts.length >= 2) {
                const config: IpConfig = {
                    id: `ip-${i + 1}`,
                    proxy: {
                        host: parts[0],
                        port: parseInt(parts[1]),
                    }
                };
                
                // Add auth if provided
                if (parts.length >= 4 && config.proxy) {
                    config.proxy.auth = {
                        username: parts[2],
                        password: parts[3]
                    };
                }
                
                ipConfigs.push(config);
            }
        }
    }
    
    // If no proxies configured, use single default IP
    if (ipConfigs.length === 0) {
        ipConfigs.push({
            id: 'ip-default',
            // No proxy = direct connection
        });
    }
    
    return new IpPool(ipConfigs);
}

