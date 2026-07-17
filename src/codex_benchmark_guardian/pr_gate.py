# ruff: noqa: E501
"""Deterministic pull-request benchmark gate artifacts."""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import asdict, dataclass

from codex_benchmark_guardian.regression import RegressionResult
from codex_benchmark_guardian.release_readiness import calculate_release_readiness
from codex_benchmark_guardian.triage import generate_triage_notes

PR_COMMENT_MARKER = "<!-- codex-benchmark-guardian:pr-gate -->"


@dataclass(frozen=True)
class PRGateResult:
    compared_metrics: int
    regression_count: int
    readiness_score: int
    readiness_label: str
    recommendation: str
    should_block: bool


def build_pr_gate_summary(results: Sequence[RegressionResult]) -> PRGateResult:
    """Build a gate result using the canonical release-readiness calculation."""
    readiness = calculate_release_readiness(results)
    regressions = sum(result.is_regression for result in results)
    return PRGateResult(
        compared_metrics=len(results),
        regression_count=regressions,
        readiness_score=readiness.score,
        readiness_label=readiness.label.value,
        recommendation=readiness.recommendation,
        should_block=readiness.label.value == "Block",
    )


def generate_gate_summary_json(summary: PRGateResult) -> str:
    """Serialize the stable gate contract with deterministic formatting."""
    return json.dumps(asdict(summary), indent=2) + "\n"


def _escape(value: object) -> str:
    return str(value).replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ")


def _find_result_by_metric_name(
    results: Sequence[RegressionResult], metric_name: str
) -> RegressionResult:
    """Find one benchmark result using a linear scan."""
    for result in results:
        if result.metric_name == metric_name:
            return result
    raise ValueError(f"unknown metric: {metric_name}")


def generate_pr_comment(
    results: Sequence[RegressionResult], summary: PRGateResult | None = None
) -> str:
    """Generate a persistent, copy-paste-ready PR comment."""
    summary = summary or build_pr_gate_summary(results)
    lines = [
        PR_COMMENT_MARKER,
        "",
        f"## Benchmark Gate: {summary.readiness_label}",
        "",
        f"**Release readiness:** {summary.readiness_score}/100",
        "",
        summary.recommendation,
        "",
        f"- Compared metrics: {summary.compared_metrics}",
        f"- Regressions: {summary.regression_count}",
        "",
    ]
    regressions = [result for result in results if result.is_regression]
    if not regressions:
        lines.extend(
            [
                "✅ Benchmark gate passed. This change is ready from a benchmark perspective.",
                "",
                "Complete Codex Handoff Pack: available as a workflow artifact.",
                "",
            ]
        )
        return "\n".join(lines)
    lines.extend(
        [
            "### Regressed metrics",
            "",
            "| Metric | Direction | Baseline | Current | Change | Severity |",
            "| --- | --- | ---: | ---: | ---: | --- |",
        ]
    )
    for regression in regressions:
        result = _find_result_by_metric_name(results, regression.metric_name)
        lines.append(
            f"| {_escape(result.metric_name)} | {_escape(result.direction.value)} | {_escape(result.baseline_value)} | {_escape(result.current_value)} | {result.change_percent:.2f}% | {_escape(result.severity)} |"
        )
    lines.extend(["", "### Regression Triage Advisor", ""])
    for note in generate_triage_notes(results):
        lines.append(
            f"- **{_escape(note.metric_name)}** — {_escape(note.likely_area)}. {_escape(note.why_it_matters)}"
        )
    lines.extend(
        [
            "",
            "### Suggested Codex investigation task",
            "",
            "Investigate the regressed benchmark paths, identify the minimal safe fix, add or update tests, and rerun the benchmark gate.",
            "",
            "### Suggested quality checks",
            "",
            "- `make lint`",
            "- `make format-check`",
            "- `make test`",
            "- `make demo-ci`",
            "",
            "Complete Codex Handoff Pack: available as a workflow artifact.",
            "",
        ]
    )
    return "\n".join(lines)
