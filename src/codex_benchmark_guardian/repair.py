"""Deterministic, bounded Codex repair contracts from benchmark evidence."""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from html import escape

from codex_benchmark_guardian.regression import RegressionResult
from codex_benchmark_guardian.release_readiness import calculate_release_readiness

REGRESSION_REPAIR_ALLOWED_ACTIONS = (
    "Inspect relevant implementation and history.",
    "Identify evidence-backed root-cause hypotheses.",
    "Implement a minimal maintainable correction.",
    "Add or update regression tests.",
    "Run approved project checks.",
    "Rerun the relevant benchmark.",
    "Review the final diff.",
)
NO_REPAIR_ALLOWED_ACTIONS = (
    "Inspect the supplied benchmark evidence.",
    "Confirm the protected workflow or trusted evaluator completed successfully.",
    "Confirm protected evidence reports zero material regressions and Ready.",
    "Review measurement stability and noise without changing protected policy.",
    "Review the final diff only when changes already exist.",
    "Report that no code repair is required.",
    "Continue monitoring benchmark stability.",
)
FORBIDDEN_ACTIONS = (
    "Lower or bypass regression thresholds.",
    "Change metric directions to suppress failures.",
    (
        "Modify, replace, rewrite, regenerate, or select different trusted benchmark "
        "evidence merely to obtain a passing result, including protected baseline evidence, "
        "trusted-harness benchmark fixtures, provenance, protected evaluator inputs, or "
        "committed metric-direction policy. Legitimate evidence collection by the protected "
        "harness remains allowed."
    ),
    "Weaken or bypass the protected benchmark harness.",
    "Weaken or bypass the protected evaluator.",
    "Delete, skip, or relax tests merely to pass.",
    "Hard-code expected benchmark results.",
    "Mark the PR Ready without protected verification.",
    "Automatically merge the PR.",
)
REQUIRED_VALIDATION_COMMANDS = (
    "make lint",
    "make format-check",
    "make test",
    "npm run lint",
    "npm run typecheck",
    "npm run build",
)
REGRESSION_COMPLETION_CRITERIA = (
    "All required project checks pass.",
    "The relevant benchmark rerun succeeds.",
    "The relevant protected benchmark workflow or trusted evaluator completes successfully.",
    "Protected evidence reports zero material regressions.",
    "Protected evidence reports readiness as Ready.",
    (
        "The protected harness, evaluator, thresholds, metric directions, and trusted "
        "evidence remain unchanged."
    ),
    "The final diff is reviewed.",
    "Human approval remains required before merge.",
)
NO_REPAIR_COMPLETION_CRITERIA = (
    "No speculative code change is made.",
    "Benchmark stability continues to be monitored.",
    "All required project checks pass.",
    "The relevant protected benchmark workflow or trusted evaluator completes successfully.",
    "Protected evidence reports zero material regressions.",
    "Protected evidence reports readiness as Ready.",
    (
        "The protected harness, evaluator, thresholds, metric directions, and trusted "
        "evidence remain unchanged."
    ),
    "The final diff is reviewed if changes were made.",
    "Human approval remains required before merge.",
)
STOP_CONDITIONS = (
    "The regression cannot be reproduced.",
    "Measurements are too noisy to support a safe conclusion.",
    "The required fix would weaken protected controls.",
    "Required context or permissions are unavailable.",
    "Validation continues to fail after reasonable repair attempts.",
    "The requested outcome cannot be achieved safely.",
)
REGRESSION_OBJECTIVE = (
    "Identify the root cause and implement the smallest maintainable fix that brings all "
    "protected harmful changes below their configured thresholds without weakening the "
    "benchmark policy."
)
NO_REPAIR_OBJECTIVE = (
    "No repair is required. Make no speculative code change and continue monitoring "
    "benchmark stability."
)
EMPTY_RESULTS_ERROR = "repair contract requires at least one benchmark result"
MARKDOWN_LITERAL_ENTITIES = {
    "!": "&#33;",
    "#": "&#35;",
    "(": "&#40;",
    ")": "&#41;",
    "*": "&#42;",
    "[": "&#91;",
    "\\": "&#92;",
    "]": "&#93;",
    "_": "&#95;",
    "`": "&#96;",
    "|": "&#124;",
}


@dataclass(frozen=True)
class RegressedMetricEvidence:
    """Canonical evidence copied from a regressed metric comparison."""

    metric_name: str
    baseline: float
    current: float
    percentage_change: float
    threshold: float
    direction: str
    severity: str


@dataclass(frozen=True)
class RepairContract:
    """Immutable repair boundaries and completion conditions for Codex."""

    repair_required: bool
    total_compared_metrics: int
    regression_count: int
    readiness_score: int
    readiness_label: str
    regressed_metrics: tuple[RegressedMetricEvidence, ...]
    repair_objective: str
    allowed_actions: tuple[str, ...]
    forbidden_actions: tuple[str, ...]
    required_validation_commands: tuple[str, ...]
    completion_criteria: tuple[str, ...]
    stop_conditions: tuple[str, ...]


def build_repair_contract(results: Sequence[RegressionResult]) -> RepairContract:
    """Build a repair contract from canonical regression and readiness results."""
    if not results:
        raise ValueError(EMPTY_RESULTS_ERROR)

    readiness = calculate_release_readiness(results)
    evidence = tuple(
        RegressedMetricEvidence(
            metric_name=result.metric_name,
            baseline=result.baseline_value,
            current=result.current_value,
            percentage_change=result.change_percent,
            threshold=result.threshold_percent,
            direction=result.direction.value,
            severity=result.severity,
        )
        for result in results
        if result.is_regression
    )
    repair_required = bool(evidence)
    return RepairContract(
        repair_required=repair_required,
        total_compared_metrics=len(results),
        regression_count=len(evidence),
        readiness_score=readiness.score,
        readiness_label=readiness.label.value,
        regressed_metrics=evidence,
        repair_objective=REGRESSION_OBJECTIVE if repair_required else NO_REPAIR_OBJECTIVE,
        allowed_actions=(
            REGRESSION_REPAIR_ALLOWED_ACTIONS if repair_required else NO_REPAIR_ALLOWED_ACTIONS
        ),
        forbidden_actions=FORBIDDEN_ACTIONS,
        required_validation_commands=REQUIRED_VALIDATION_COMMANDS,
        completion_criteria=(
            REGRESSION_COMPLETION_CRITERIA if repair_required else NO_REPAIR_COMPLETION_CRITERIA
        ),
        stop_conditions=STOP_CONDITIONS,
    )


def _as_contract(value: Sequence[RegressionResult] | RepairContract) -> RepairContract:
    if isinstance(value, RepairContract):
        if value.total_compared_metrics == 0:
            raise ValueError(EMPTY_RESULTS_ERROR)
        return value
    return build_repair_contract(value)


def _render_metric_name(value: str) -> str:
    """Render an untrusted metric name as inert literal text in a Markdown table."""
    visible_value = value.replace("\r", "\\r").replace("\n", "\\n")
    safe_value = "".join(
        MARKDOWN_LITERAL_ENTITIES.get(character, escape(character, quote=True))
        for character in visible_value
    )
    return f"<code>{safe_value}</code>"


def _bullet_section(title: str, values: tuple[str, ...], *, code: bool = False) -> list[str]:
    rendered = (f"`{value}`" for value in values) if code else iter(values)
    return [f"## {title}", "", *(f"- {value}" for value in rendered), ""]


def _decision_lines(contract: RepairContract) -> list[str]:
    return [
        f"- **Repair required:** {'Yes' if contract.repair_required else 'No'}",
        f"- **Compared metrics:** {contract.total_compared_metrics}",
        f"- **Regressions:** {contract.regression_count}",
        f"- **Readiness:** {contract.readiness_label} ({contract.readiness_score}/100)",
    ]


def _evidence_lines(contract: RepairContract) -> list[str]:
    lines = [
        "| Metric | Baseline | Current | Change | Threshold | Direction | Severity |",
        "| --- | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    lines.extend(
        "| "
        f"{_render_metric_name(metric.metric_name)} | "
        f"{metric.baseline:g} | {metric.current:g} | "
        f"{metric.percentage_change:.2f}% | {metric.threshold:.2f}% | "
        f"{metric.direction} | {metric.severity} |"
        for metric in contract.regressed_metrics
    )
    if not contract.regressed_metrics:
        lines.append("| None | — | — | — | — | — | — |")
    return lines


def generate_repair_contract_markdown(
    value: Sequence[RegressionResult] | RepairContract,
) -> str:
    """Render a deterministic human-readable repair contract."""
    contract = _as_contract(value)
    lines = ["# Codex Repair Contract", "", "## Current Benchmark Decision", ""]
    lines.extend([*_decision_lines(contract), "", "## Regressed Metric Evidence", ""])
    lines.extend([*_evidence_lines(contract), "", "## Repair Objective", ""])
    lines.extend([contract.repair_objective, ""])
    lines.extend(_bullet_section("Allowed Actions", contract.allowed_actions))
    lines.extend(_bullet_section("Forbidden Actions", contract.forbidden_actions))
    lines.extend(
        _bullet_section(
            "Required Validation Commands", contract.required_validation_commands, code=True
        )
    )
    lines.extend(_bullet_section("Completion Criteria", contract.completion_criteria))
    lines.extend(_bullet_section("Stop Conditions", contract.stop_conditions))
    return "\n".join(lines)


def generate_repair_contract_json(
    value: Sequence[RegressionResult] | RepairContract,
) -> str:
    """Render a deterministic JSON repair contract."""
    return json.dumps(asdict(_as_contract(value)), indent=2) + "\n"


def generate_codex_repair_goal(
    value: Sequence[RegressionResult] | RepairContract,
) -> str:
    """Render a bounded repair goal suitable for a Codex goal thread."""
    contract = _as_contract(value)
    lines = ["# Codex Benchmark Repair Goal", "", "## Current Benchmark Decision", ""]
    lines.extend([*_decision_lines(contract), "", "## Regressed Metrics", ""])
    lines.extend([*_evidence_lines(contract), "", "## Bounded Objective", ""])
    lines.extend([contract.repair_objective, ""])
    lines.extend(_bullet_section("Allowed Actions", contract.allowed_actions))
    lines.extend(_bullet_section("Prohibited Changes", contract.forbidden_actions))
    lines.extend(
        _bullet_section("Required Validation", contract.required_validation_commands, code=True)
    )
    lines.extend(_bullet_section("Finish Conditions", contract.completion_criteria))
    lines.extend(_bullet_section("Stop-and-Report Conditions", contract.stop_conditions))
    if contract.repair_required:
        final_instruction = (
            "Inspect, repair, review, validate, and repeat until every finish condition "
            "passes or a stop-and-report condition applies. Do not prescribe or force a "
            "code change without evidence."
        )
    else:
        final_instruction = (
            "Inspect and verify the supplied protected evidence without making speculative "
            "code or test changes. Confirm the protected workflow or trusted evaluator "
            "completed successfully and that protected evidence reports zero material "
            "regressions and Ready. Preserve human approval before merge. Report that no "
            "code repair is required, and continue monitoring benchmark stability."
        )
    lines.extend([final_instruction, ""])
    return "\n".join(lines)
