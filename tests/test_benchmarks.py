from __future__ import annotations

import json

import pytest

from codex_benchmark_guardian.benchmarks import compare_benchmark_metrics, load_benchmark_file


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
