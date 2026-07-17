import json
import math
import subprocess
import sys
from pathlib import Path

COMMON_METRICS = {
    "comparison_latency_ms",
    "report_generation_latency_ms",
    "comparison_throughput_metrics_per_second",
}


def _run_harness(tmp_path: Path, mode: str, output_name: str) -> dict[str, float]:
    output = tmp_path / "nested" / output_name
    subprocess.run(
        [
            sys.executable,
            "benchmarks/run_project_benchmarks.py",
            "--output",
            str(output),
            "--workload-size",
            "4",
            "--iterations",
            "1",
            "--warmups",
            "0",
            "--benchmark-mode",
            mode,
            "--operation-repetitions",
            "2",
        ],
        check=True,
    )
    return json.loads(output.read_text())


def test_benchmark_runner_writes_numeric_metrics_with_directions(tmp_path) -> None:
    metrics = _run_harness(tmp_path, "full-pr-gate", "metrics.json")
    directions = json.loads(Path("benchmarks/directions.json").read_text())

    assert set(metrics) == {*COMMON_METRICS, "pr_gate_generation_latency_ms"}
    assert set(metrics) == set(directions)
    assert all(
        isinstance(value, (int, float)) and math.isfinite(value) for value in metrics.values()
    )


def test_benchmark_modes_emit_expected_metric_sets(tmp_path) -> None:
    common = _run_harness(tmp_path, "bootstrap-common", "common.json")
    full = _run_harness(tmp_path, "full-pr-gate", "full.json")

    assert set(common) == COMMON_METRICS
    assert set(full) == {*COMMON_METRICS, "pr_gate_generation_latency_ms"}
    assert all(
        isinstance(value, (int, float)) and math.isfinite(value)
        for metrics in (common, full)
        for value in metrics.values()
    )
