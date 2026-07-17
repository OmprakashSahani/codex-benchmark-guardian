"""Run reproducible, mode-controlled Codex Benchmark Guardian benchmarks."""

from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path

from codex_benchmark_guardian.benchmarks import compare_benchmark_metrics
from codex_benchmark_guardian.regression import MetricDirection
from codex_benchmark_guardian.report import generate_html_report, generate_markdown_report

COMMON_METRIC_NAMES = (
    "comparison_latency_ms",
    "report_generation_latency_ms",
    "comparison_throughput_metrics_per_second",
)
FULL_METRIC_NAMES = (
    *COMMON_METRIC_NAMES[:2],
    "pr_gate_generation_latency_ms",
    COMMON_METRIC_NAMES[2],
)


def _workload(size: int):
    baseline = {f"metric_{index}": float(index + 100) for index in range(size)}
    current = {
        name: value * (1.25 if index % 4 == 0 else 1.15 if index % 4 == 1 else 1.05)
        for index, (name, value) in enumerate(baseline.items())
    }
    return baseline, current


def _batch(operation, repetitions: int) -> int:
    start = time.perf_counter_ns()
    for _ in range(repetitions):
        operation()
    return time.perf_counter_ns() - start


def _measure(size: int, mode: str, repetitions: int) -> dict[str, float]:
    baseline, current = _workload(size)
    results = compare_benchmark_metrics(baseline, current, 10, MetricDirection.HIGHER_IS_WORSE)
    comparison_ns = _batch(
        lambda: compare_benchmark_metrics(baseline, current, 10, MetricDirection.HIGHER_IS_WORSE),
        repetitions,
    )
    report_ns = _batch(
        lambda: (generate_markdown_report(results), generate_html_report(results)), repetitions
    )
    metrics = {
        "comparison_latency_ms": comparison_ns / repetitions / 1_000_000,
        "report_generation_latency_ms": report_ns / repetitions / 1_000_000,
        "comparison_throughput_metrics_per_second": size
        * repetitions
        / (comparison_ns / 1_000_000_000),
    }
    if mode == "full-pr-gate":
        try:
            from codex_benchmark_guardian.pr_gate import build_pr_gate_summary, generate_pr_comment
        except ImportError as exc:
            raise RuntimeError(
                "full-pr-gate mode requires codex_benchmark_guardian.pr_gate"
            ) from exc
        gate_ns = _batch(
            lambda: generate_pr_comment(results, build_pr_gate_summary(results)), repetitions
        )
        metrics["pr_gate_generation_latency_ms"] = gate_ns / repetitions / 1_000_000
    return metrics


def run_benchmarks(
    size: int, iterations: int, warmups: int, mode: str, repetitions: int
) -> dict[str, float]:
    if size < 1 or iterations < 1 or warmups < 0 or repetitions < 1:
        raise ValueError("invalid benchmark dimensions")
    for _ in range(warmups):
        _measure(size, mode, repetitions)
    samples = [_measure(size, mode, repetitions) for _ in range(iterations)]
    names = FULL_METRIC_NAMES if mode == "full-pr-gate" else COMMON_METRIC_NAMES
    return {name: statistics.median(sample[name] for sample in samples) for name in names}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workload-size", type=int, default=50)
    parser.add_argument("--iterations", type=int, default=7)
    parser.add_argument("--warmups", type=int, default=2)
    parser.add_argument(
        "--benchmark-mode", choices=("bootstrap-common", "full-pr-gate"), default="full-pr-gate"
    )
    parser.add_argument("--operation-repetitions", type=int, default=50)
    args = parser.parse_args()
    metrics = run_benchmarks(
        args.workload_size,
        args.iterations,
        args.warmups,
        args.benchmark_mode,
        args.operation_repetitions,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
