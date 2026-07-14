from __future__ import annotations

import json

import pytest

from codex_benchmark_guardian.benchmarks import (
    compare_benchmark_metrics,
    load_benchmark_file,
    load_directions_config,
)
from codex_benchmark_guardian.regression import MetricDirection


def test_load_benchmark_file_loads_numeric_metrics(tmp_path) -> None:
    benchmark_path = tmp_path / "benchmark.json"
    benchmark_path.write_text(
        json.dumps(
            {
                "latency_ms": 100.0,
                "memory_mb": 256,
                "ignored": "not numeric",
                "also_ignored": True,
            }
        ),
        encoding="utf-8",
    )

    metrics = load_benchmark_file(benchmark_path)

    assert metrics == {
        "latency_ms": 100.0,
        "memory_mb": 256.0,
    }


def test_load_benchmark_file_rejects_non_object_json(tmp_path) -> None:
    benchmark_path = tmp_path / "benchmark.json"
    benchmark_path.write_text("[]", encoding="utf-8")

    with pytest.raises(ValueError, match="benchmark JSON must contain an object"):
        load_benchmark_file(benchmark_path)


def test_compare_benchmark_metrics_compares_multiple_matching_metrics() -> None:
    results = compare_benchmark_metrics(
        baseline_metrics={
            "latency_ms": 100.0,
            "memory_mb": 256.0,
            "baseline_only": 1.0,
        },
        current_metrics={
            "latency_ms": 125.0,
            "memory_mb": 260.0,
            "current_only": 1.0,
        },
        threshold_percent=10.0,
    )

    assert [result.metric_name for result in results] == ["latency_ms", "memory_mb"]
    assert results[0].is_regression is True
    assert results[0].severity == "high"
    assert results[1].is_regression is False
    assert results[1].severity == "none"


def test_compare_benchmark_metrics_uses_mixed_directions_config() -> None:
    results = compare_benchmark_metrics(
        baseline_metrics={"latency_ms": 100.0, "throughput_rps": 1000.0},
        current_metrics={"latency_ms": 125.0, "throughput_rps": 850.0},
        threshold_percent=10.0,
        directions={"throughput_rps": MetricDirection.LOWER_IS_WORSE},
    )

    assert [result.metric_name for result in results] == ["latency_ms", "throughput_rps"]
    assert [result.direction for result in results] == [
        MetricDirection.HIGHER_IS_WORSE,
        MetricDirection.LOWER_IS_WORSE,
    ]
    assert [result.is_regression for result in results] == [True, True]


def test_compare_benchmark_metrics_falls_back_to_global_direction() -> None:
    results = compare_benchmark_metrics(
        baseline_metrics={"requests_ok": 1000.0, "throughput_rps": 1000.0},
        current_metrics={"requests_ok": 850.0, "throughput_rps": 850.0},
        threshold_percent=10.0,
        direction=MetricDirection.LOWER_IS_WORSE,
        directions={"throughput_rps": MetricDirection.LOWER_IS_WORSE},
    )

    assert [result.direction for result in results] == [
        MetricDirection.LOWER_IS_WORSE,
        MetricDirection.LOWER_IS_WORSE,
    ]
    assert all(result.is_regression for result in results)


def test_compare_benchmark_metrics_falls_back_to_higher_is_worse_by_default() -> None:
    results = compare_benchmark_metrics(
        baseline_metrics={"latency_ms": 100.0, "throughput_rps": 1000.0},
        current_metrics={"latency_ms": 125.0, "throughput_rps": 850.0},
        threshold_percent=10.0,
        directions={"throughput_rps": MetricDirection.LOWER_IS_WORSE},
    )

    latency_result = results[0]
    assert latency_result.metric_name == "latency_ms"
    assert latency_result.direction == MetricDirection.HIGHER_IS_WORSE
    assert latency_result.is_regression is True


def test_load_directions_config_rejects_invalid_direction(tmp_path) -> None:
    directions_path = tmp_path / "directions.json"
    directions_path.write_text(
        '{"latency_ms": "sideways_is_worse"}',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="invalid direction for latency_ms"):
        load_directions_config(directions_path)


def test_load_directions_config_loads_metric_directions(tmp_path) -> None:
    directions_path = tmp_path / "directions.json"
    directions_path.write_text(
        json.dumps(
            {
                "latency_ms": "higher_is_worse",
                "throughput_rps": "lower_is_worse",
            }
        ),
        encoding="utf-8",
    )

    assert load_directions_config(directions_path) == {
        "latency_ms": MetricDirection.HIGHER_IS_WORSE,
        "throughput_rps": MetricDirection.LOWER_IS_WORSE,
    }
