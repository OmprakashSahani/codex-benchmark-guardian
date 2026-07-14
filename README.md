# Codex Benchmark Guardian

Codex Benchmark Guardian is a CLI-first Python developer tool for comparing benchmark results, detecting performance regressions, and generating Markdown and optional HTML reports for software reliability workflows.

Built for OpenAI Build Week, it helps teams turn raw benchmark numbers into clear pass/fail signals that can be reviewed locally, shared in pull requests, or enforced in CI.

## Why this project

Performance regressions are easy to miss when benchmark data lives in logs, ad hoc scripts, or disconnected JSON files. Codex Benchmark Guardian provides a small, review-friendly workflow for identifying changes before they reach users.

The project focuses on:

- Fast feedback for developers running local benchmark comparisons.
- Clear regression thresholds that make performance changes easier to discuss.
- Markdown reports that fit naturally into GitHub issues, pull requests, and CI summaries.
- Optional self-contained HTML reports for browser-friendly benchmark reviews.
- Regression Triage Advisor guidance that explains likely areas, why each regression matters, and what to check next.
- Simple JSON inputs so teams can integrate existing benchmark output without adopting a large platform.

## Features

- `cbg about` and `cbg version` commands for project metadata.
- Single-metric comparison with configurable regression thresholds and metric direction support.
- JSON benchmark loading from baseline and current result files.
- Multi-metric benchmark comparison across matching numeric metrics.
- Regression detection with severity classification for `higher_is_worse` and `lower_is_worse` metrics.
- Markdown report generation with summary counts, per-metric status, and regression triage guidance.
- Optional HTML report generation with summary counts, per-metric status tables, and regression triage guidance.
- CI-friendly failure mode for benchmark regressions with `--fail-on-regression`.
- Example benchmark files under `examples/`.
- Pytest and Ruff quality checks wired for developer workflows and CI.

## Installation

Codex Benchmark Guardian requires Python 3.12 or newer.

Install the project in editable mode with development dependencies:

```bash
pip install -e ".[dev]"
```

## Quickstart

Run the project information command:

```bash
cbg about
```

Compare a single benchmark metric where higher values are worse, which is the default behavior:

```bash
cbg compare latency_ms 100 125 --threshold 10
```

Compare a metric where lower values are worse, such as throughput:

```bash
cbg compare throughput_rps 1000 850 --threshold 10 --direction lower_is_worse
```

Compare benchmark JSON files and generate a Markdown report:

```bash
cbg compare-files examples/baseline.json examples/current.json --threshold 10 --report reports/report.md
```

Use `--direction lower_is_worse` as a global fallback for a file comparison when decreasing metric values represent regressions:

```bash
cbg compare-files examples/baseline.json examples/current.json --threshold 10 --direction lower_is_worse --report reports/report.md
```

For mixed benchmark files, pass a directions config that maps each metric to its direction:

```bash
cbg compare-files examples/baseline.json examples/current.json --threshold 10 --directions-config examples/directions.json --report reports/report.md
```

Generate Markdown and HTML reports from the same comparison:

```bash
cbg compare-files examples/baseline.json examples/current.json --threshold 10 --report reports/report.md --html-report reports/report.html
```

Run a CI-style smoke check with data that should not regress:

```bash
cbg compare-files examples/baseline.json examples/current_no_regression.json --threshold 10 --report reports/report.md --fail-on-regression
```

The `--fail-on-regression` flag preserves normal report generation, then exits with a non-zero status code if regressions were found. This is useful in CI workflows where benchmark regressions should block a pull request or deployment. Without the flag, `compare-files` keeps the existing behavior and exits successfully even when regressions are reported.

## Metric direction

By default, Codex Benchmark Guardian treats higher current values as worse. This matches latency, runtime, and memory metrics: a regression is detected when the current value increases by at least the configured threshold percentage.

Some metrics are better when they are higher, such as throughput or requests per second. For those, pass `--direction lower_is_worse`; a regression is detected when the current value decreases by at least the threshold percentage. For `compare-files`, you can also pass `--directions-config` to configure direction per metric while keeping `--direction` as the fallback for metrics missing from the config.

Supported directions are:

- `higher_is_worse` — default; current value increases can regress.
- `lower_is_worse` — current value decreases can regress.

The actual direction used for each metric is shown in CLI output and in Markdown and HTML reports. When regressions are detected, the Regression Triage Advisor adds deterministic developer guidance for common metric patterns such as latency, runtime, memory, throughput, accuracy, recall, precision, and success rate.

Example `examples/directions.json`:

```json
{
  "latency_ms": "higher_is_worse",
  "memory_mb": "higher_is_worse",
  "runtime_s": "higher_is_worse",
  "throughput_rps": "lower_is_worse"
}
```

## Example output

Single-metric comparison output:

```text
Metric: latency_ms
Baseline: 100.0
Current: 125.0
Change: 25.00%
Threshold: 10.00%
Direction: higher_is_worse
Regression detected | Severity: high
```

File comparison output:

```text
Compared 4 metrics
Regressions detected: 2
Report written to: reports/report.md
```

When `--html-report reports/report.html` is provided, the command also writes a self-contained HTML report and prints its path. When `--fail-on-regression` is provided and regressions are detected, the command prints a failure message after writing reports and exits non-zero.

## Report example

The `compare-files` command writes a Markdown report like this. When `--html-report` is provided, it also writes a browser-friendly HTML report with the same summary and table data:

```markdown
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
```

## Built with Codex

Codex was used to help implement and refine the core developer workflow for this project, including:

- JSON benchmark comparison between baseline and current files.
- CLI integration for single-metric and file-based comparisons.
- Regression report generation in Markdown and optional HTML.
- Regression Triage Advisor notes for developer-facing remediation guidance.
- Unit and CLI tests for benchmark loading, comparison, and regression detection.
- Example benchmark inputs and generated report output.
- GitHub Actions CI configuration for automated quality checks.

## Project structure

```text
.
├── .github/workflows/ci.yml      # GitHub Actions quality checks
├── examples/                     # Example benchmark JSON files
│   ├── baseline.json
│   ├── current.json
│   └── current_no_regression.json
├── reports/                      # Generated Markdown report examples
│   └── report.md
├── src/codex_benchmark_guardian/ # CLI and benchmark comparison package
│   ├── benchmarks.py
│   ├── cli.py
│   ├── regression.py
│   ├── report.py
│   └── triage.py
├── tests/                        # Pytest suite
├── pyproject.toml                # Package metadata and tool configuration
└── README.md
```


## Makefile commands

For a shorter local workflow, the repository includes a simple `Makefile` with common development and demo commands:

```bash
make install        # Install the project with development dependencies
make lint           # Run Ruff lint checks
make format-check   # Verify Ruff formatting
make test           # Run the pytest suite
make demo           # Generate Markdown and HTML reports from the example benchmarks
make demo-ci        # Run a passing CI-style smoke check with regression failure enabled
make demo-ci-fail   # Demonstrate expected CI failure handling for regressions
make clean-reports  # Remove generated report files
```

`make demo` compares `examples/baseline.json` and `examples/current.json` to show a regression report without failing the command. `make demo-ci` compares `examples/baseline.json` and `examples/current_no_regression.json` as a passing CI-style smoke check with `--fail-on-regression`. `make demo-ci-fail` intentionally compares the regressing `examples/current.json` file with `--fail-on-regression`, handles the expected non-zero exit gracefully, and prints a confirmation message. All demo targets apply per-metric directions from `examples/directions.json` and write `reports/report.md` plus `reports/report.html`.

## Quality checks

Run the same checks used for local development and CI:

```bash
ruff check .
ruff format --check .
pytest
```

For CI enforcement, add `--fail-on-regression` to `cbg compare-files` so the job fails when the comparison finds regressions.
