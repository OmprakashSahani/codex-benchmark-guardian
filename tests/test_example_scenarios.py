import json
import math
from pathlib import Path

import pytest

from codex_benchmark_guardian.benchmarks import (
    compare_benchmark_metrics,
    load_benchmark_file,
    load_directions_config,
)
from codex_benchmark_guardian.pr_gate import build_pr_gate_summary
from codex_benchmark_guardian.regression import MetricDirection

SCENARIO_ROOT = Path(__file__).parents[1] / "examples" / "scenarios"
CATALOGUE = json.loads((SCENARIO_ROOT / "scenarios.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("scenario", CATALOGUE, ids=lambda item: item["id"])
def test_scenario_files_are_valid_engine_inputs(scenario: dict[str, object]) -> None:
    paths = [
        SCENARIO_ROOT / str(scenario[key])
        for key in ("baseline_path", "current_path", "directions_path")
    ]
    assert all(path.is_file() for path in paths)

    baseline_json = json.loads(paths[0].read_text(encoding="utf-8"))
    current_json = json.loads(paths[1].read_text(encoding="utf-8"))
    directions_json = json.loads(paths[2].read_text(encoding="utf-8"))
    assert isinstance(baseline_json, dict) and baseline_json
    assert isinstance(current_json, dict) and current_json
    assert isinstance(directions_json, dict)
    assert baseline_json.keys() == current_json.keys()
    for metrics in (baseline_json, current_json):
        assert all(
            not isinstance(value, bool) and isinstance(value, int | float) and math.isfinite(value)
            for value in metrics.values()
        )

    baseline = load_benchmark_file(paths[0])
    current = load_benchmark_file(paths[1])
    directions = load_directions_config(paths[2])

    assert baseline and current
    assert baseline.keys() == current.keys()
    assert all(value != 0 and math.isfinite(value) for value in baseline.values())
    assert all(math.isfinite(value) for value in current.values())
    assert directions.keys() == baseline.keys()
    assert set(directions.values()) <= set(MetricDirection)
    assert MetricDirection(str(scenario["fallback_direction"])) in set(MetricDirection)


@pytest.mark.parametrize("scenario", CATALOGUE, ids=lambda item: item["id"])
def test_scenario_matches_documented_results(scenario: dict[str, object]) -> None:
    baseline = load_benchmark_file(SCENARIO_ROOT / str(scenario["baseline_path"]))
    current = load_benchmark_file(SCENARIO_ROOT / str(scenario["current_path"]))
    directions = load_directions_config(SCENARIO_ROOT / str(scenario["directions_path"]))
    results = compare_benchmark_metrics(
        baseline,
        current,
        float(scenario["threshold_percent"]),
        MetricDirection(str(scenario["fallback_direction"])),
        directions,
    )
    summary = build_pr_gate_summary(results)

    assert summary.compared_metrics == scenario["expected_compared_metric_count"]
    assert summary.regression_count == scenario["expected_regression_count"]
    assert summary.readiness_score == scenario["expected_readiness_score"]
    assert summary.readiness_label == scenario["expected_readiness_label"]


def test_pr_regression_metric_matches_documented_evidence() -> None:
    scenario = next(item for item in CATALOGUE if item["id"] == "pr-20-regression")
    results = compare_benchmark_metrics(
        load_benchmark_file(SCENARIO_ROOT / scenario["baseline_path"]),
        load_benchmark_file(SCENARIO_ROOT / scenario["current_path"]),
        scenario["threshold_percent"],
        MetricDirection(scenario["fallback_direction"]),
        load_directions_config(SCENARIO_ROOT / scenario["directions_path"]),
    )
    regressions = [result for result in results if result.is_regression]

    assert len(regressions) == 1
    assert regressions[0].metric_name == "pr_gate_generation_latency_ms"
    assert regressions[0].change_percent == pytest.approx(135.21, abs=0.01)
    assert regressions[0].severity == "critical"
