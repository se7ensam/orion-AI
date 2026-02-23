## Benchmark & Stress Testing Plan

### 1. Purpose

This plan defines how to benchmark and stress test the Orion ingestion backend to:

- **Measure throughput** (jobs/hour, jobs/second)
- **Characterize latency** for each processing stage
- **Validate stability** under sustained load
- **Detect bottlenecks** in:
  - SEC downloads
  - HTML cleaning and chunking
  - Database writes
  - RabbitMQ queue handling

It is designed to be repeatable and to serve as a baseline for future optimizations.

---

### 2. Key Metrics

- **Worker metrics**
  - Jobs processed per minute / hour
  - Per-stage latency:
    - `downloadTimeMs`
    - `cleaningTimeMs`
    - `chunkingTimeMs`
    - `storageTimeMs`
    - `totalTimeMs`
  - Chunk statistics:
    - `chunksCreated`
    - `rawHtmlSize`
    - `cleanTextSize`
  - Success vs failure vs rate‑limit retries

- **Queue metrics (RabbitMQ)**
  - Queue depth over time
  - Consumer count
  - Message ACK / NACK rates

- **Database metrics (PostgreSQL)**
  - Inserts/sec into `filings` and `filing_chunks`
  - Slow queries / lock contention
  - Connection pool utilization (idle/total/waiting)

- **Rate limiting metrics**
  - 429 occurrences
  - Throttler stats: `totalRequests`, `blockedCount`, `isCurrentlyBlocked`

---

### 3. Test Environments

- **Local development**
  - `docker-compose up -d`
  - Suitable for functional and low/medium load tests.

- **Staging / pre‑prod**
  - Same topology as production.
  - Recommended to use a **mock SEC service** for high‑volume tests to avoid hitting real SEC.gov.
  - Override `SEC_API_BASE` to point to the mock when load testing.

---

### 4. Test Data

- **Realistic**
  - Use existing scripts:
    - `scripts/seed-queue/fetch-master-idx.ts`
    - `scripts/seed-queue/filter-filings.ts`
  - Target: 500–2,000 filings to represent a realistic window.

- **Synthetic / mock**
  - Create JSON files of `IngestionJob`s with controlled characteristics:
    - Small HTML: ~50 KB
    - Medium HTML: ~500 KB
    - Large HTML: 5–10 MB
  - Point jobs at:
    - Real SEC (low volume, ≤ 100 jobs)
    - Mock SEC server (for heavy stress)

---

### 5. Scenarios

#### Scenario A – Baseline Functional

**Goal**: Validate correctness and capture initial metrics.

- **Config**
  - `WORKER_CONCURRENCY=1`
  - `DB_POOL_SIZE=10`
  - `LOG_LEVEL=INFO`

- **Steps**
  1. `make docker-up`
  2. `make migrate`
  3. Seed ~100 jobs:
     - `make seed-fetch`
     - `make seed-filter`
     - `make seed-push`
  4. `make worker-start`
  5. Observe:
     - Worker logs (per‑stage timings)
     - `make status`
     - `make verify`

- **Record**
  - Avg `totalTimeMs` per job
  - Avg and p95 `downloadTimeMs`, `storageTimeMs`
  - Chunk counts per filing

---

#### Scenario B – Throughput Ramp‑Up

**Goal**: Measure how throughput and latency change as load increases.

- **Matrix**

| Run | Jobs | WORKER_CONCURRENCY | DB_POOL_SIZE |
|-----|------|--------------------|--------------|
| B1  | 500  | 1                  | 10           |
| B2  | 1,000| 1                  | 20           |
| B3  | 2,000| 2                  | 20           |

- **Steps (per run)**
  1. `make docker-up` (or ensure stack is running)
  2. Seed N jobs with `make seed-fetch`, `make seed-filter`, tweak filter or input if needed, then `make seed-push`.
  3. `make worker-start` (or restart worker between runs)
  4. During processing:
     - Monitor queue depth via RabbitMQ UI (`http://localhost:15672`)
     - Run `make status` at start, mid, and end
     - Watch for rate limit logs

- **Metrics**
  - Total wall‑clock time to drain queue
  - Jobs/hour
  - CPU and memory usage of worker container
  - DB pool stats (from metrics logs)

---

#### Scenario C – Large Filings (Worst‑Case)

**Goal**: Stress CPU, memory, and DB with large HTML inputs.

- **Data**
  - 100–200 jobs pointing at large (~5–10 MB) HTML (use mock SEC if possible).

- **Config**
  - `WORKER_CONCURRENCY=1`
  - `DB_POOL_SIZE=20`
  - `LOG_LEVEL=INFO`

- **Focus**
  - `cleaningTimeMs`
  - `chunkingTimeMs`
  - `storageTimeMs`
  - Peak memory usage

- **Record**
  - Average and p95 total processing latency
  - Maximum chunks per filing
  - DB insert throughput

---

#### Scenario D – Soak Test (Stability)

**Goal**: Detect memory leaks, connection leaks, and long‑term instability.

- **Plan**
  - Duration: 2–4 hours
  - Push small batches of jobs periodically (e.g., 100 jobs every 5–10 minutes).

- **Steps**
  1. Start stack: `make docker-up`
  2. Start worker: `make worker-start`
  3. Every 5–10 minutes:
     - `make seed-push` (using a prepared `filings-6k.json` or synthetic dataset)
  4. Every 15–30 minutes:
     - `make status`
     - `docker stats` on worker container
     - Capture metrics summaries from logs

- **Watch for**
  - Gradual memory creep
  - Increasing number of stuck `PROCESSING` filings
  - Escalating error or rate‑limit events

---

#### Scenario E – Failure & Recovery

**Goal**: Validate resilience and correct behavior under failures.

- **Cases**
  1. **Worker crash**
     - While processing jobs, kill worker container or process.
     - Restart worker.
     - Verify:
       - No data corruption
       - Jobs are either re‑processed or correctly marked failed.

  2. **Database outage**
     - Stop PostgreSQL container temporarily.
     - Observe worker behavior (error logs, backoff).
     - Bring DB back up.
     - Verify worker recovers without manual intervention.

  3. **Rate‑limit storm**
     - Use mock SEC to deliberately return 429s.
     - Verify:
       - Throttler logs block periods
       - Jobs are re‑queued as designed
       - No tight retry loops

---

### 6. How to Run & Record

For each scenario:

1. **Capture configuration**
   - `.env` settings: `WORKER_CONCURRENCY`, `DB_POOL_SIZE`, `METRICS_INTERVAL_MS`, `LOG_LEVEL`.
   - Number and type of jobs.

2. **Run scenario**
   - Use `make` targets where possible:
     - `make docker-up`, `make migrate`, `make seed-*`, `make worker-start`, `make status`, `make verify`.

3. **Collect metrics**
   - Worker logs (structured metrics and timings).
   - `make status` output.
   - `make verify` output.
   - `docker stats` snapshot for CPU/memory.

4. **Summarize results**
   - Create a simple table for each run:

| Scenario | Jobs | Concurrency | Pool Size | Total Time | Jobs/hour | Avg Latency | p95 Latency | Errors | Notes |
|----------|------|------------|-----------|------------|-----------|------------|------------|--------|-------|

Store summaries in a separate file such as `BENCHMARK_RESULTS.md` or a spreadsheet.

---

### 7. Interpreting Results

- **Throughput**
  - Compare jobs/hour across configurations.
  - Identify diminishing returns when increasing concurrency or pool size.

- **Latency**
  - Focus on p95 and p99 rather than just average.
  - Look for specific stages (download, store) that dominate total time.

- **Stability**
  - No increasing trend in memory or open connections.
  - Consistent error rates and quick recovery from transient failures.

- **Rate Limiting**
  - Ensure 429s are rare in normal scenarios.
  - Throttler stats should show relatively low `blockedCount` under typical loads.

---

### 8. Next Steps

Once baseline benchmarks are captured:

- Use profiler + metrics to pinpoint slowest stages.
- Consider:
  - Further DB indexing based on real query patterns.
  - Adjusting `WORKER_CONCURRENCY` and `DB_POOL_SIZE` based on observed sweet spots.
  - Adding Prometheus/Grafana integration for continuous monitoring.

