# Benchmark Comparison Report

Compared metrics: 4
Regressions detected: 2

| Metric | Direction | Baseline | Current | Change | Threshold | Status | Severity |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| latency_ms | higher_is_worse | 100 | 125 | 25.00% | 10.00% | Regression | high |
| memory_mb | higher_is_worse | 256 | 260 | 1.56% | 10.00% | OK | none |
| runtime_s | higher_is_worse | 2.5 | 2.7 | 8.00% | 10.00% | OK | none |
| throughput_rps | lower_is_worse | 1000 | 850 | -15.00% | 10.00% | Regression | medium |

## Regression Triage

### latency_ms

- **Likely area:** Request path latency or dependency wait time
- **Why it matters:** Higher latency slows developer and user workflows and can hide downstream bottlenecks.
- **Suggested checks:**
  - Inspect recent changes on the hot path for added I/O, sleeps, retries, or serialization work.
  - Compare dependency timing, network calls, database queries, and cache hit rates against the baseline.
  - Check benchmark host load and input size to rule out environmental noise.

### throughput_rps

- **Likely area:** Capacity, concurrency, or request processing rate
- **Why it matters:** Lower throughput means the system handles less work with the same resources.
- **Suggested checks:**
  - Review concurrency limits, worker counts, queue behavior, and backpressure changes.
  - Inspect CPU, lock contention, database pool usage, and external service rate limits.
  - Verify the benchmark duration and request mix match the baseline run.

