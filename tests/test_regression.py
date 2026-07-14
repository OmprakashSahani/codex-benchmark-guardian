import pytest

from codex_benchmark_guardian.regression import (
    MetricDirection,
    calculate_change_percent,
    classify_severity,
    detect_regression,
)


def test_calculate_change_percent() -> None:
    change = calculate_change_percent(baseline_value=100.0, current_value=120.0)

    assert change == 20.0


def test_calculate_change_percent_rejects_zero_baseline() -> None:
    with pytest.raises(ValueError, match="baseline_value must not be zero"):
        calculate_change_percent(baseline_value=0.0, current_value=120.0)


def test_classify_severity() -> None:
    assert classify_severity(5.0) == "low"
    assert classify_severity(10.0) == "medium"
    assert classify_severity(25.0) == "high"
    assert classify_severity(50.0) == "critical"


def test_detect_regression_when_threshold_exceeded() -> None:
    result = detect_regression(
        metric_name="latency_ms",
        baseline_value=100.0,
        current_value=125.0,
        threshold_percent=10.0,
    )

    assert result.metric_name == "latency_ms"
    assert result.baseline_value == 100.0
    assert result.current_value == 125.0
    assert result.change_percent == 25.0
    assert result.threshold_percent == 10.0
    assert result.is_regression is True
    assert result.severity == "high"


def test_detect_regression_when_threshold_not_exceeded() -> None:
    result = detect_regression(
        metric_name="latency_ms",
        baseline_value=100.0,
        current_value=105.0,
        threshold_percent=10.0,
    )

    assert result.is_regression is False
    assert result.severity == "none"


def test_detect_lower_is_worse_regression_when_threshold_exceeded() -> None:
    result = detect_regression(
        metric_name="throughput_rps",
        baseline_value=1000.0,
        current_value=850.0,
        threshold_percent=10.0,
        direction=MetricDirection.LOWER_IS_WORSE,
    )

    assert result.change_percent == -15.0
    assert result.direction == MetricDirection.LOWER_IS_WORSE
    assert result.is_regression is True
    assert result.severity == "medium"


def test_detect_lower_is_worse_no_regression_when_value_increases() -> None:
    result = detect_regression(
        metric_name="throughput_rps",
        baseline_value=1000.0,
        current_value=1100.0,
        threshold_percent=10.0,
        direction=MetricDirection.LOWER_IS_WORSE,
    )

    assert result.change_percent == 10.0
    assert result.is_regression is False
    assert result.severity == "none"
