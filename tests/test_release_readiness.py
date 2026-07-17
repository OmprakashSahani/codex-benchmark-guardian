import pytest

from codex_benchmark_guardian.regression import RegressionResult
from codex_benchmark_guardian.release_readiness import (
    ReleaseReadinessLabel,
    calculate_release_readiness,
)


def _regression(severity: str) -> RegressionResult:
    return RegressionResult(
        metric_name=f"{severity}_metric",
        baseline_value=100.0,
        current_value=125.0,
        change_percent=25.0,
        threshold_percent=10.0,
        is_regression=True,
        severity=severity,
    )


def test_calculate_release_readiness_without_regressions() -> None:
    readiness = calculate_release_readiness([])

    assert readiness.score == 100
    assert readiness.label is ReleaseReadinessLabel.READY
    assert readiness.recommendation == (
        "No blocking benchmark regressions detected. Continue monitoring benchmark stability."
    )


def test_calculate_release_readiness_deducts_low_medium_and_high_regressions() -> None:
    readiness = calculate_release_readiness(
        [_regression("low"), _regression("medium"), _regression("high")]
    )

    assert readiness.score == 40
    assert readiness.label is ReleaseReadinessLabel.BLOCK


def test_calculate_release_readiness_never_drops_below_zero() -> None:
    readiness = calculate_release_readiness([_regression("high")] * 4)

    assert readiness.score == 0


@pytest.mark.parametrize(
    ("results", "score", "label"),
    [
        ([], 100, ReleaseReadinessLabel.READY),
        ([_regression("low")], 90, ReleaseReadinessLabel.READY),
        ([_regression("medium"), _regression("low")], 70, ReleaseReadinessLabel.NEEDS_REVIEW),
        ([_regression("high"), _regression("low")], 60, ReleaseReadinessLabel.BLOCK),
    ],
)
def test_calculate_release_readiness_classification_boundaries(results, score, label) -> None:
    readiness = calculate_release_readiness(results)

    assert readiness.score == score
    assert readiness.label is label
