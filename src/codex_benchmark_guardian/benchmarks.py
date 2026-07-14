from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from codex_benchmark_guardian.regression import (
    MetricDirection,
    RegressionResult,
    detect_regression,
)

BenchmarkMetrics = dict[str, float]


def load_benchmark_file(path: Path) -> BenchmarkMetrics:
    """Load numeric benchmark metrics from a JSON file."""
    with path.open(encoding="utf-8") as benchmark_file:
        data: Any = json.load(benchmark_file)

    if not isinstance(data, dict):
        raise ValueError("benchmark JSON must contain an object of metric names to numeric values")

    metrics: BenchmarkMetrics = {}
    for metric_name, metric_value in data.items():
        if not isinstance(metric_name, str):
            raise ValueError("benchmark metric names must be strings")
        if isinstance(metric_value, bool) or not isinstance(metric_value, int | float):
            continue
        metrics[metric_name] = float(metric_value)

    return metrics


def compare_benchmark_metrics(
    baseline_metrics: BenchmarkMetrics,
    current_metrics: BenchmarkMetrics,
    threshold_percent: float,
    direction: MetricDirection = MetricDirection.HIGHER_IS_WORSE,
) -> list[RegressionResult]:
    """Compare matching numeric metrics from two benchmark mappings."""
    metric_names = sorted(baseline_metrics.keys() & current_metrics.keys())
    results: list[RegressionResult] = []
    for metric_name in metric_names:
        results.append(
            detect_regression(
                metric_name=metric_name,
                baseline_value=baseline_metrics[metric_name],
                current_value=current_metrics[metric_name],
                threshold_percent=threshold_percent,
                direction=direction,
            )
        )

    return results
