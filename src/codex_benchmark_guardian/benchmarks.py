from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from codex_benchmark_guardian.regression import (
    MetricDirection,
    RegressionResult,
    detect_regression,
)

BenchmarkMetrics = dict[str, float]
MetricDirections = dict[str, MetricDirection]


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


def load_directions_config(path: Path) -> MetricDirections:
    """Load per-metric direction settings from a JSON file."""
    with path.open(encoding="utf-8") as directions_file:
        data: Any = json.load(directions_file)

    if not isinstance(data, dict):
        raise ValueError("directions config JSON must contain an object")

    directions: MetricDirections = {}
    for metric_name, direction_value in data.items():
        if not isinstance(metric_name, str):
            raise ValueError("directions config metric names must be strings")
        if not isinstance(direction_value, str):
            raise ValueError(f"direction for {metric_name} must be a string")
        try:
            directions[metric_name] = MetricDirection(direction_value)
        except ValueError as exc:
            valid_directions = ", ".join(direction.value for direction in MetricDirection)
            raise ValueError(
                f"invalid direction for {metric_name}: {direction_value}. "
                f"Expected one of: {valid_directions}"
            ) from exc

    return directions


def compare_benchmark_metrics(
    baseline_metrics: BenchmarkMetrics,
    current_metrics: BenchmarkMetrics,
    threshold_percent: float,
    direction: MetricDirection = MetricDirection.HIGHER_IS_WORSE,
    directions: Mapping[str, MetricDirection] | None = None,
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
                direction=directions.get(metric_name, direction) if directions else direction,
            )
        )

    return results
