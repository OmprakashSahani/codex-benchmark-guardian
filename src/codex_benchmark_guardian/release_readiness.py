"""Deterministic release-readiness scoring for benchmark comparisons."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

from codex_benchmark_guardian.regression import RegressionResult


class ReleaseReadinessLabel(StrEnum):
    """Merge recommendation classification derived from the readiness score."""

    READY = "Ready"
    NEEDS_REVIEW = "Needs Review"
    BLOCK = "Block"


@dataclass(frozen=True)
class ReleaseReadiness:
    """A deterministic benchmark-based release recommendation."""

    score: int
    label: ReleaseReadinessLabel
    recommendation: str


SEVERITY_DEDUCTIONS = {"high": 30, "medium": 20, "low": 10, "critical": 30}
RECOMMENDATIONS = {
    ReleaseReadinessLabel.READY: (
        "No blocking benchmark regressions detected. Continue monitoring benchmark stability."
    ),
    ReleaseReadinessLabel.NEEDS_REVIEW: "Benchmark regressions require review before merging.",
    ReleaseReadinessLabel.BLOCK: (
        "Do not merge until high-impact benchmark regressions are investigated."
    ),
}


def calculate_release_readiness(results: Sequence[RegressionResult]) -> ReleaseReadiness:
    """Calculate the score, classification, and recommendation from regressions.

    Critical regressions receive the high-severity deduction so existing regression
    classifications remain conservatively represented in the score.
    """
    deductions = sum(
        SEVERITY_DEDUCTIONS.get(result.severity, 0) for result in results if result.is_regression
    )
    score = max(0, 100 - deductions)
    if score >= 90:
        label = ReleaseReadinessLabel.READY
    elif score >= 70:
        label = ReleaseReadinessLabel.NEEDS_REVIEW
    else:
        label = ReleaseReadinessLabel.BLOCK
    return ReleaseReadiness(score=score, label=label, recommendation=RECOMMENDATIONS[label])


def generate_release_readiness_markdown(
    results: Sequence[RegressionResult],
) -> str:
    """Generate a standalone Markdown release-readiness handoff artifact."""
    readiness = calculate_release_readiness(results)
    return "\n".join(
        [
            "# Benchmark Release Readiness",
            "",
            f"- **Readiness:** {readiness.label.value}",
            f"- **Score:** {readiness.score}/100",
            f"- **Recommendation:** {readiness.recommendation}",
            "",
        ]
    )
