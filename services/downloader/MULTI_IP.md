# Multi-IP Parallel Processing

The downloader now supports parallel processing across multiple IP addresses to dramatically increase download speed.

## How It Works

- **Single IP**: 10 req/sec limit = ~4.75 filings/sec = ~60 minutes for 16,190 filings
- **Multiple IPs**: Each IP gets 10 req/sec = N IPs × 10 req/sec = N× faster downloads

## Configuration

### Option 1: Environment Variable (Recommended)

Set the `IP_PROXIES` environment variable with your proxy list:

```bash
# Format: host1:port1:user1:pass1,host2:port2:user2:pass2
# Or without auth: host1:port1,host2:port2

export IP_PROXIES="proxy1.example.com:8080:user1:pass1,proxy2.example.com:8080:user2:pass2,proxy3.example.com:8080"
```

### Option 2: Direct IP Binding (Advanced)

For direct IP binding, you'll need to modify `ipPool.ts` to configure `localAddress` for each IP.

## Performance

| IPs | Rate Limit | Filings/sec | Time for 16,190 |
|-----|------------|-------------|------------------|
| 1   | 9.5 req/sec | ~4.75      | ~60 minutes      |
| 3   | 28.5 req/sec | ~14.25     | ~19 minutes      |
| 5   | 47.5 req/sec | ~23.75     | ~11 minutes      |
| 10  | 95 req/sec   | ~47.5      | ~6 minutes       |

## Example Usage

```bash
# Single IP (default)
python -m src.cli download --start-year 2009 --end-year 2010

# Multi-IP (with proxies)
export IP_PROXIES="proxy1:8080,proxy2:8080,proxy3:8080"
python -m src.cli download --start-year 2009 --end-year 2010
```

## Features

- ✅ Automatic IP rotation (round-robin)
- ✅ Per-IP rate limiting (10 req/sec per IP)
- ✅ Load balancing across IPs
- ✅ Request statistics per IP
- ✅ Automatic failover on errors

## Notes

- Each IP must have its own proxy or network interface
- SEC rate limit is per IP, so multiple IPs = multiple rate limits
- Proxy authentication is supported
- The system automatically detects and uses available IPs

