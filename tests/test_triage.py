from codex_benchmark_guardian.regression import MetricDirection, RegressionResult
from codex_benchmark_guardian.triage import generate_triage_notes


def regressed_result(metric_name: str) -> RegressionResult:
    return RegressionResult(
        metric_name=metric_name,
        baseline_value=100.0,
        current_value=125.0,
        change_percent=25.0,
        threshold_percent=10.0,
        is_regression=True,
        severity="high",
    )


def test_latency_regression_triage() -> None:
    notes = generate_triage_notes([regressed_result("latency_ms")])

    assert len(notes) == 1
    assert notes[0].metric_name == "latency_ms"
    assert notes[0].likely_area == "Request path latency or dependency wait time"
    assert "Higher latency" in notes[0].why_it_matters
    assert any("hot path" in check for check in notes[0].suggested_checks)


def test_throughput_regression_triage() -> None:
    result = RegressionResult(
        metric_name="throughput_rps",
        baseline_value=1000.0,
        current_value=850.0,
        change_percent=-15.0,
        threshold_percent=10.0,
        is_regression=True,
        severity="medium",
        direction=MetricDirection.LOWER_IS_WORSE,
    )

    notes = generate_triage_notes([result])

    assert len(notes) == 1
    assert notes[0].likely_area == "Capacity, concurrency, or request processing rate"
    assert "Lower throughput" in notes[0].why_it_matters
    assert any("concurrency" in check for check in notes[0].suggested_checks)


def test_memory_regression_triage() -> None:
    notes = generate_triage_notes([regressed_result("memory_mb")])

    assert len(notes) == 1
    assert notes[0].likely_area == "Memory allocation, object retention, or working-set growth"
    assert "Higher memory" in notes[0].why_it_matters
    assert any("allocation" in check for check in notes[0].suggested_checks)


def test_unknown_metric_fallback_triage() -> None:
    notes = generate_triage_notes([regressed_result("custom_score")])

    assert len(notes) == 1
    assert notes[0].likely_area == "Metric-specific benchmark behavior"
    assert "configured threshold" in notes[0].why_it_matters
    assert any("metric direction" in check for check in notes[0].suggested_checks)


def test_triage_notes_include_regressed_metrics_only() -> None:
    ok_result = RegressionResult(
        metric_name="runtime_s",
        baseline_value=100.0,
        current_value=101.0,
        change_percent=1.0,
        threshold_percent=10.0,
        is_regression=False,
        severity="none",
    )

    assert generate_triage_notes([ok_result]) == []
