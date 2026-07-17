import json
import math
import subprocess
import sys
from pathlib import Path


def test_benchmark_runner_writes_numeric_metrics_with_directions(tmp_path) -> None:
    output = tmp_path / "nested" / "metrics.json"
    subprocess.run(
        [
            sys.executable,
            "benchmarks/run_project_benchmarks.py",
            "--output",
            str(output),
            "--workload-size",
            "8",
            "--iterations",
            "2",
            "--warmups",
            "1",
        ],
        check=True,
    )
    metrics = json.loads(output.read_text())
    directions = json.loads(Path("benchmarks/directions.json").read_text())
    assert set(metrics) == {
        "comparison_latency_ms",
        "report_generation_latency_ms",
        "pr_gate_generation_latency_ms",
        "comparison_throughput_metrics_per_second",
    }
    assert set(metrics) == set(directions)
    assert all(
        isinstance(value, (int, float)) and math.isfinite(value) for value in metrics.values()
    )


def test_benchmark_modes_emit_expected_metric_sets() -> None:
    from benchmarks.run_project_benchmarks import run_benchmarks

    common = run_benchmarks(4, 1, 0, "bootstrap-common", 2)
    full = run_benchmarks(4, 1, 0, "full-pr-gate", 2)
    assert set(common) == {
        "comparison_latency_ms",
        "report_generation_latency_ms",
        "comparison_throughput_metrics_per_second",
    }
    assert set(full) == {*common, "pr_gate_generation_latency_ms"}
