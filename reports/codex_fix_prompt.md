# Codex Benchmark Guardian

## Codex Fix Prompt

Total compared metrics: 4
Regressions detected: 2

Benchmark regressions were detected. Use this prompt to investigate and prepare a minimal, well-tested fix.

## Regressed Metrics

| Metric | Direction | Baseline | Current | Change | Severity |
| --- | --- | ---: | ---: | ---: | --- |
| latency_ms | higher_is_worse | 100 | 125 | 25.00% | high |
| throughput_rps | lower_is_worse | 1000 | 850 | -15.00% | medium |

## Regression Triage Guidance

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

## Task for Codex

Inspect this repository and the benchmark results above. Identify possible causes for any regression, propose a minimal fix, add or update tests that cover the behavior, and run the project checks before finishing.

Suggested quality checks:

- `make lint`
- `make format-check`
- `make test`
- `make demo-ci`
