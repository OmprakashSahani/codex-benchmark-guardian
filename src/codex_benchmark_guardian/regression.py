from __future__ import annotations

from dataclasses import dataclass


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


def calculate_change_percent(baseline_value: float, current_value: float) -> float:
    """Calculate percentage change from baseline to current value."""
    if baseline_value == 0:
        raise ValueError("baseline_value must not be zero")

    return ((current_value - baseline_value) / baseline_value) * 100


def classify_severity(change_percent: float) -> str:
    """Classify regression severity based on percentage change."""
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
) -> RegressionResult:
    """
    Detect whether a benchmark metric regressed.

    For now, higher values are treated as worse.
    Example: latency, runtime, memory usage.
    """
    change_percent = calculate_change_percent(
        baseline_value=baseline_value,
        current_value=current_value,
    )

    is_regression = change_percent >= threshold_percent

    severity = classify_severity(change_percent) if is_regression else "none"

    return RegressionResult(
        metric_name=metric_name,
        baseline_value=baseline_value,
        current_value=current_value,
        change_percent=change_percent,
        threshold_percent=threshold_percent,
        is_regression=is_regression,
        severity=severity,
    )
