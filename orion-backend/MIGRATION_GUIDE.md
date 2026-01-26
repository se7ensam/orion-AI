# Migration Guide - Optimized Ingestion Worker

This guide explains how to migrate to the optimized version of the ingestion worker.

## What Changed?

### Breaking Changes
**None** - All changes are backward compatible. Existing data and queue messages will work without modification.

### API Changes
The repository API has changed, but the old methods are replaced by a single transactional method:

**Before:**
```typescript
const filingId = await repository.saveFiling(job, rawHtml);
await repository.saveChunks(filingId, chunks);
await repository.updateStatus(filingId, 'COMPLETED');
```

**After:**
```typescript
await repository.saveFilingWithChunks(job, rawHtml, chunks);
```

## Migration Steps

### 1. Rebuild the Application

```bash
cd orion-backend/services/ingestion-worker
npm run build
```

### 2. Apply Optional Database Indexes (Recommended)

For better query performance, apply the additional indexes:

```bash
# Using psql
psql $DATABASE_URL -f ../../shared/database/migrations/002_add_performance_indexes.sql

# Or using docker if running in containers
docker exec -i orion-postgres psql -U orion -d orion < shared/database/migrations/002_add_performance_indexes.sql
```

**Note**: These indexes are optional but recommended. The application works fine without them.

### 3. Deploy with Zero Downtime

The worker now supports graceful shutdown, allowing zero-downtime deployments:

#### Option A: Manual Restart
```bash
# Send SIGTERM to trigger graceful shutdown
kill -TERM <worker_pid>

# Worker will:
# 1. Stop accepting new messages
# 2. Complete in-flight messages
# 3. Print final metrics
# 4. Close all connections
# 5. Exit cleanly

# Start new worker
npm start
```

#### Option B: Docker/Kubernetes
The worker respects SIGTERM signals, so standard rolling updates work:

```bash
docker-compose restart ingestion-worker
# or
kubectl rollout restart deployment/ingestion-worker
```

#### Option C: Systemd
```bash
systemctl restart ingestion-worker
```

### 4. Monitor Metrics (New Feature)

After deployment, you'll see periodic metrics reports in the logs:

```
═══════════════════════════════════════
📊 INGESTION WORKER METRICS SUMMARY
═══════════════════════════════════════
Total Jobs:          250
Successful:          248 (99.20%)
Failed:              2
Rate Limit Errors:   0
───────────────────────────────────────
Avg Processing Time: 3200ms
Min Processing Time: 1100ms
Max Processing Time: 7800ms
Avg Download Time:   2100ms
Avg Storage Time:    850ms
Avg Chunks/Job:      142
═══════════════════════════════════════
```

These appear:
- Every 5 minutes automatically
- On graceful shutdown (final summary)

## Verification

### 1. Check Build Success
```bash
cd services/ingestion-worker
npm run build
# Should complete with no errors
```

### 2. Verify Worker Startup
```bash
npm start
```

Look for:
```
Connecting to RabbitMQ...
Waiting for messages in ingestion_jobs...
```

### 3. Test Graceful Shutdown
In another terminal:
```bash
# Find the worker process
ps aux | grep "node.*ingestion-worker"

# Send SIGTERM
kill -TERM <pid>
```

Should see:
```
Received SIGTERM signal
Initiating graceful shutdown...
📊 Final Metrics Summary:
...
Cancelling consumer...
Waiting for in-flight messages to complete...
Closing RabbitMQ channel...
Closing RabbitMQ connection...
Closing database connection pool...
Graceful shutdown complete
```

### 4. Verify Transactional Integrity

Check that filings and chunks are saved atomically:

```sql
-- This should return 0 (no orphaned filings)
SELECT COUNT(*) 
FROM filings f 
WHERE f.status = 'COMPLETED' 
  AND NOT EXISTS (
    SELECT 1 FROM filing_chunks fc WHERE fc.filing_id = f.id
  );
```

## Rollback Plan

If you need to rollback for any reason:

### Option 1: Git Revert
```bash
git checkout HEAD~1 -- services/ingestion-worker/src
cd services/ingestion-worker
npm run build
npm start
```

### Option 2: Keep Optimizations, Adjust Configuration

If specific optimization causes issues, you can adjust:

#### Reduce Connection Pool Size
Edit `services/ingestion-worker/src/queue/consumer.ts`:
```typescript
this.pool = new Pool({ 
    connectionString: ENV.DATABASE_URL,
    max: 10, // Reduced from 20
    idleTimeoutMillis: 30000,
    connectionTimeoutMillis: 2000,
});
```

#### Disable Metrics Reporting
Comment out in `services/ingestion-worker/src/queue/consumer.ts`:
```typescript
// this.startMetricsReporting();
```

## Troubleshooting

### Issue: Worker won't shutdown gracefully

**Symptom**: Worker hangs on SIGTERM

**Solution**: 
- Check for long-running database queries
- Verify RabbitMQ connection is healthy
- Wait up to 10 seconds before force-killing

### Issue: Higher memory usage initially

**Symptom**: Worker uses more memory than before

**Cause**: Metrics collector stores last 1000 job stats

**Solution**: Reduce `maxStoredMetrics` in `monitoring/metrics.ts`:
```typescript
private readonly maxStoredMetrics: number = 100; // Reduced from 1000
```

### Issue: Database deadlocks

**Symptom**: Transaction errors in logs

**Cause**: Multiple workers competing for same resources

**Solution**: 
- Check database connection limits
- Reduce worker pool size or worker count
- Ensure database has sufficient connections: `max_connections` > (workers × pool size)

### Issue: Metrics not appearing

**Symptom**: No metrics summary after 5 minutes

**Cause**: Worker processing very slowly or no messages

**Solution**: 
- Check if messages are in queue: `rabbitmqadmin list queues`
- Verify worker is connected to RabbitMQ
- Check worker logs for errors

## Performance Tuning

### Adjust Connection Pool Size

Based on your workload:

```typescript
// Low volume (<100 jobs/hour)
max: 5

// Medium volume (100-1000 jobs/hour)
max: 10

// High volume (>1000 jobs/hour)
max: 20
```

### Adjust Metrics Reporting Interval

In `services/ingestion-worker/src/queue/consumer.ts`:

```typescript
// More frequent (every 2 minutes)
this.metricsInterval = setInterval(() => {
    metricsCollector.printSummary();
}, 2 * 60 * 1000);

// Less frequent (every 15 minutes)
this.metricsInterval = setInterval(() => {
    metricsCollector.printSummary();
}, 15 * 60 * 1000);
```

### Increase Message Prefetch

For better throughput with multiple worker instances:

```typescript
await this.channel.prefetch(3); // Process 3 messages concurrently
```

**Note**: Requires careful testing to ensure database can handle the load.

## Questions?

Refer to:
- `OPTIMIZATIONS.md` - Detailed optimization descriptions
- Worker logs - Real-time metrics and error messages
- Database logs - Transaction and query performance

## Checklist

- [ ] Code builds successfully (`npm run build`)
- [ ] Worker starts without errors (`npm start`)
- [ ] Graceful shutdown works (send SIGTERM)
- [ ] Metrics appear in logs after 5 minutes
- [ ] Database indexes applied (optional)
- [ ] No orphaned filings in database
- [ ] Connection pool stats look healthy
- [ ] Success rate > 95% in metrics
