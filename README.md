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
- Simple JSON inputs so teams can integrate existing benchmark output without adopting a large platform.

## Features

- `cbg about` and `cbg version` commands for project metadata.
- Single-metric comparison with configurable regression thresholds.
- JSON benchmark loading from baseline and current result files.
- Multi-metric benchmark comparison across matching numeric metrics.
- Regression detection with severity classification.
- Markdown report generation with summary counts and per-metric status.
- Optional HTML report generation with summary counts and per-metric status tables.
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

Compare a single benchmark metric:

```bash
cbg compare latency_ms 100 125 --threshold 10
```

Compare benchmark JSON files and generate a Markdown report:

```bash
cbg compare-files examples/baseline.json examples/current.json --threshold 10 --report reports/report.md
```

Generate Markdown and HTML reports from the same comparison:

```bash
cbg compare-files examples/baseline.json examples/current.json --threshold 10 --report reports/report.md --html-report reports/report.html
```

## Example output

Single-metric comparison output:

```text
Metric: latency_ms
Baseline: 100.0
Current: 125.0
Change: 25.00%
Threshold: 10.00%
Regression detected | Severity: high
```

File comparison output:

```text
Compared 3 metrics
Regressions detected: 1
Report written to: reports/report.md
```

When `--html-report reports/report.html` is provided, the command also writes a self-contained HTML report and prints its path.

## Report example

The `compare-files` command writes a Markdown report like this. When `--html-report` is provided, it also writes a browser-friendly HTML report with the same summary and table data:

```markdown
# Benchmark Comparison Report

Compared metrics: 3
Regressions detected: 1

| Metric | Baseline | Current | Change | Threshold | Status | Severity |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| latency_ms | 100 | 125 | 25.00% | 10.00% | Regression | high |
| memory_mb | 256 | 260 | 1.56% | 10.00% | OK | none |
| runtime_s | 2.5 | 2.7 | 8.00% | 10.00% | OK | none |
```

## Built with Codex

Codex was used to help implement and refine the core developer workflow for this project, including:

- JSON benchmark comparison between baseline and current files.
- CLI integration for single-metric and file-based comparisons.
- Regression report generation in Markdown and optional HTML.
- Unit and CLI tests for benchmark loading, comparison, and regression detection.
- Example benchmark inputs and generated report output.
- GitHub Actions CI configuration for automated quality checks.

## Project structure

```text
.
├── .github/workflows/ci.yml      # GitHub Actions quality checks
├── examples/                     # Example benchmark JSON files
│   ├── baseline.json
│   └── current.json
├── reports/                      # Generated Markdown report examples
│   └── report.md
├── src/codex_benchmark_guardian/ # CLI and benchmark comparison package
│   ├── benchmarks.py
│   ├── cli.py
│   ├── regression.py
│   └── report.py
├── tests/                        # Pytest suite
├── pyproject.toml                # Package metadata and tool configuration
└── README.md
```

## Quality checks

Run the same checks used for local development and CI:

```bash
ruff check .
ruff format --check .
pytest
```
