from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class MetricDirection(StrEnum):
    """Direction that defines which metric movement is considered worse."""

    HIGHER_IS_WORSE = "higher_is_worse"
    LOWER_IS_WORSE = "lower_is_worse"


@dataclass(frozen=True)
class RegressionResult:
    """Result of comparing a current benchmark value against a baseline."""

    metric_name: str
    baseline_value: float
    current_value: float
    change_percent: float
    threshold_percent: float
    is_regression: bool
    severity: str
    direction: MetricDirection = MetricDirection.HIGHER_IS_WORSE


def calculate_change_percent(baseline_value: float, current_value: float) -> float:
    """Calculate percentage change from baseline to current value."""
    if baseline_value == 0:
        raise ValueError("baseline_value must not be zero")

    return ((current_value - baseline_value) / baseline_value) * 100


def classify_severity(change_percent: float) -> str:
    """Classify regression severity based on regression percentage magnitude."""
    change_percent = abs(change_percent)
    if change_percent >= 50:
        return "critical"
    if change_percent >= 25:
        return "high"
    if change_percent >= 10:
        return "medium"
    return "low"


def detect_regression(
    metric_name: str,
    baseline_value: float,
    current_value: float,
    threshold_percent: float = 10.0,
    direction: MetricDirection = MetricDirection.HIGHER_IS_WORSE,
) -> RegressionResult:
    """Detect whether a benchmark metric regressed for the configured direction."""
    change_percent = calculate_change_percent(
        baseline_value=baseline_value,
        current_value=current_value,
    )

    if direction == MetricDirection.HIGHER_IS_WORSE:
        is_regression = change_percent >= threshold_percent
    else:
        is_regression = change_percent <= -threshold_percent

    severity = classify_severity(change_percent) if is_regression else "none"

    return RegressionResult(
        metric_name=metric_name,
        baseline_value=baseline_value,
        current_value=current_value,
        change_percent=change_percent,
        threshold_percent=threshold_percent,
        is_regression=is_regression,
        severity=severity,
        direction=direction,
    )
