from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from codex_benchmark_guardian.benchmarks import (
    compare_benchmark_metrics,
    load_benchmark_file,
    load_directions_config,
)
from codex_benchmark_guardian.ci import generate_github_actions_workflow
from codex_benchmark_guardian.regression import MetricDirection
from codex_benchmark_guardian.report import (
    generate_codex_fix_prompt,
    generate_github_issue,
    generate_html_report,
    generate_markdown_report,
)


@dataclass(frozen=True)
class HandoffPackPaths:
    report: Path
    html_report: Path
    codex_fix_prompt: Path
    github_issue: Path
    ci_workflow: Path


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
    directions = (
        load_directions_config(directions_config_path)
        if directions_config_path is not None
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
    )
    paths.report.write_text(generate_markdown_report(results), encoding="utf-8")
    paths.html_report.write_text(generate_html_report(results), encoding="utf-8")
    paths.codex_fix_prompt.write_text(generate_codex_fix_prompt(results), encoding="utf-8")
    paths.github_issue.write_text(generate_github_issue(results), encoding="utf-8")
    paths.ci_workflow.write_text(
        generate_github_actions_workflow(
            baseline_path=baseline_path,
            current_path=current_path,
            directions_config_path=directions_config_path,
            threshold=threshold,
            direction=direction,
        ),
        encoding="utf-8",
    )
    return paths
