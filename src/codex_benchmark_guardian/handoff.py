from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from codex_benchmark_guardian.benchmarks import (
    compare_benchmark_metrics,
    load_benchmark_file,
    load_directions_config,
)
from codex_benchmark_guardian.ci import generate_github_actions_workflow
from codex_benchmark_guardian.pr_gate import (
    build_pr_gate_summary,
    generate_gate_summary_json,
    generate_pr_comment,
)
from codex_benchmark_guardian.regression import MetricDirection
from codex_benchmark_guardian.release_readiness import generate_release_readiness_markdown
from codex_benchmark_guardian.repair import (
    build_repair_contract,
    generate_codex_repair_goal,
    generate_repair_contract_json,
    generate_repair_contract_markdown,
)
from codex_benchmark_guardian.report import (
    generate_codex_fix_prompt,
    generate_github_issue,
    generate_html_report,
    generate_markdown_report,
)

DEFAULT_BASELINE_PATH = Path("examples/baseline.json")
DEFAULT_CURRENT_PATH = Path("examples/current.json")
DEFAULT_DIRECTIONS_CONFIG_PATH = Path("examples/directions.json")


def _normalized_path(path: Path) -> Path:
    return path.expanduser().resolve(strict=False)


def resolve_handoff_directions_config_path(
    *,
    baseline_path: Path,
    current_path: Path,
    directions_config_path: Path | None,
) -> Path | None:
    """Return the directions config path that handoff-pack should use."""
    if directions_config_path is not None:
        return directions_config_path
    if _normalized_path(baseline_path) == _normalized_path(
        DEFAULT_BASELINE_PATH
    ) and _normalized_path(current_path) == _normalized_path(DEFAULT_CURRENT_PATH):
        return DEFAULT_DIRECTIONS_CONFIG_PATH
    return None


@dataclass(frozen=True)
class HandoffPackPaths:
    report: Path
    html_report: Path
    codex_fix_prompt: Path
    github_issue: Path
    ci_workflow: Path
    release_readiness: Path
    pr_comment: Path
    gate_summary: Path
    repair_contract: Path
    repair_contract_json: Path
    codex_repair_goal: Path


def generate_handoff_pack(
    *,
    baseline_path: Path,
    current_path: Path,
    directions_config_path: Path | None,
    threshold: float,
    direction: MetricDirection,
    output_dir: Path,
) -> HandoffPackPaths:
    """Generate a complete benchmark regression developer handoff pack."""
    baseline_metrics = load_benchmark_file(baseline_path)
    current_metrics = load_benchmark_file(current_path)
    effective_directions_config_path = resolve_handoff_directions_config_path(
        baseline_path=baseline_path,
        current_path=current_path,
        directions_config_path=directions_config_path,
    )
    directions = (
        load_directions_config(effective_directions_config_path)
        if effective_directions_config_path is not None
        else None
    )
    results = compare_benchmark_metrics(
        baseline_metrics=baseline_metrics,
        current_metrics=current_metrics,
        threshold_percent=threshold,
        direction=direction,
        directions=directions,
    )
    if not results:
        msg = "no matching numeric metrics found"
        raise ValueError(msg)

    output_dir.mkdir(parents=True, exist_ok=True)
    paths = HandoffPackPaths(
        report=output_dir / "report.md",
        html_report=output_dir / "report.html",
        codex_fix_prompt=output_dir / "codex_fix_prompt.md",
        github_issue=output_dir / "github_issue.md",
        ci_workflow=output_dir / "benchmark_guardian_ci.yml",
        release_readiness=output_dir / "release_readiness.md",
        pr_comment=output_dir / "pr_comment.md",
        gate_summary=output_dir / "gate_summary.json",
        repair_contract=output_dir / "repair_contract.md",
        repair_contract_json=output_dir / "repair_contract.json",
        codex_repair_goal=output_dir / "codex_repair_goal.md",
    )
    paths.report.write_text(generate_markdown_report(results), encoding="utf-8")
    paths.html_report.write_text(generate_html_report(results), encoding="utf-8")
    paths.codex_fix_prompt.write_text(generate_codex_fix_prompt(results), encoding="utf-8")
    paths.github_issue.write_text(generate_github_issue(results), encoding="utf-8")
    paths.release_readiness.write_text(
        generate_release_readiness_markdown(results), encoding="utf-8"
    )
    gate_summary = build_pr_gate_summary(results)
    paths.pr_comment.write_text(generate_pr_comment(results, gate_summary), encoding="utf-8")
    paths.gate_summary.write_text(generate_gate_summary_json(gate_summary), encoding="utf-8")
    repair_contract = build_repair_contract(results)
    paths.repair_contract.write_text(
        generate_repair_contract_markdown(repair_contract), encoding="utf-8"
    )
    paths.repair_contract_json.write_text(
        generate_repair_contract_json(repair_contract), encoding="utf-8"
    )
    paths.codex_repair_goal.write_text(
        generate_codex_repair_goal(repair_contract), encoding="utf-8"
    )
    paths.ci_workflow.write_text(
        generate_github_actions_workflow(
            baseline_path=baseline_path,
            current_path=current_path,
            directions_config_path=effective_directions_config_path,
            threshold=threshold,
            direction=direction,
        ),
        encoding="utf-8",
    )
    return paths
