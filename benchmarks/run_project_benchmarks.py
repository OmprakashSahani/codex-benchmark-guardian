"""Run reproducible in-environment Codex Benchmark Guardian benchmarks."""

from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path

from codex_benchmark_guardian.benchmarks import compare_benchmark_metrics

try:
    from codex_benchmark_guardian.pr_gate import build_pr_gate_summary, generate_pr_comment
except ImportError:
    build_pr_gate_summary = None
    generate_pr_comment = None

from codex_benchmark_guardian.regression import MetricDirection
from codex_benchmark_guardian.release_readiness import generate_release_readiness_markdown
from codex_benchmark_guardian.report import generate_html_report, generate_markdown_report

METRIC_NAMES = (
    "comparison_latency_ms",
    "report_generation_latency_ms",
    "pr_gate_generation_latency_ms",
    "comparison_throughput_metrics_per_second",
)


def _workload(size: int):
    baseline = {f"metric_{index}": float(index + 100) for index in range(size)}
    current = {name: value * 1.02 for name, value in baseline.items()}
    return baseline, current


def _measure(workload_size: int) -> dict[str, float]:
    baseline, current = _workload(workload_size)
    start = time.perf_counter_ns()
    results = compare_benchmark_metrics(baseline, current, 10, MetricDirection.HIGHER_IS_WORSE)
    comparison_ns = time.perf_counter_ns() - start
    start = time.perf_counter_ns()
    generate_markdown_report(results)
    generate_html_report(results)
    report_ns = time.perf_counter_ns() - start
    start = time.perf_counter_ns()
    if build_pr_gate_summary is not None and generate_pr_comment is not None:
        summary = build_pr_gate_summary(results)
        generate_pr_comment(results, summary)
    else:
        # Initial rollout compatibility: main has readiness generation but no PR gate module.
        generate_release_readiness_markdown(results)
    gate_ns = time.perf_counter_ns() - start
    return {
        "comparison_latency_ms": comparison_ns / 1_000_000,
        "report_generation_latency_ms": report_ns / 1_000_000,
        "pr_gate_generation_latency_ms": gate_ns / 1_000_000,
        "comparison_throughput_metrics_per_second": workload_size / (comparison_ns / 1_000_000_000),
    }


def run_benchmarks(workload_size: int, iterations: int, warmups: int) -> dict[str, float]:
    """Measure deterministic work with warmups and median measurements."""
    if workload_size < 1 or iterations < 1 or warmups < 0:
        raise ValueError(
            "workload-size and iterations must be positive; warmups cannot be negative"
        )
    for _ in range(warmups):
        _measure(workload_size)
    samples = [_measure(workload_size) for _ in range(iterations)]
    return {name: statistics.median(sample[name] for sample in samples) for name in METRIC_NAMES}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workload-size", type=int, default=500)
    parser.add_argument("--iterations", type=int, default=7)
    parser.add_argument("--warmups", type=int, default=2)
    args = parser.parse_args()
    metrics = run_benchmarks(args.workload_size, args.iterations, args.warmups)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
