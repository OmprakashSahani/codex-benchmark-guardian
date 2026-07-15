from __future__ import annotations

import shlex
from dataclasses import dataclass
from pathlib import Path

from codex_benchmark_guardian.regression import MetricDirection

DEFAULT_BASELINE_PATH = Path("examples/baseline.json")
DEFAULT_CURRENT_PATH = Path("examples/current_no_regression.json")
DASHBOARD_SAMPLE_CURRENT_PATH = Path("examples/current.json")
DASHBOARD_UPLOAD_BASELINE_PATH = Path("benchmarks/baseline.json")
DASHBOARD_UPLOAD_CURRENT_PATH = Path("benchmarks/current.json")
DASHBOARD_UPLOAD_DIRECTIONS_CONFIG_PATH = Path("benchmarks/directions.json")
DEFAULT_DIRECTIONS_CONFIG_PATH = Path("examples/directions.json")
DEFAULT_OUTPUT_PATH = Path(".github/workflows/benchmark-guardian.yml")
DEFAULT_PYTHON_VERSION = "3.12"
DEFAULT_THRESHOLD = 10.0
DEFAULT_MARKDOWN_REPORT_PATH = Path("reports/report.md")
DEFAULT_HTML_REPORT_PATH = Path("reports/report.html")
DEFAULT_CODEX_PROMPT_PATH = Path("reports/codex_fix_prompt.md")


@dataclass(frozen=True)
class DashboardWorkflowContext:
    """Repository paths and notes for dashboard-generated CI workflows."""

    baseline_path: Path
    current_path: Path
    directions_config_path: Path | None
    note: str


def select_dashboard_workflow_context(
    *, use_sample_data: bool, has_directions_upload: bool
) -> DashboardWorkflowContext:
    """Select deterministic CI workflow paths that match the dashboard input source."""
    if use_sample_data:
        return DashboardWorkflowContext(
            baseline_path=DEFAULT_BASELINE_PATH,
            current_path=DASHBOARD_SAMPLE_CURRENT_PATH,
            directions_config_path=DEFAULT_DIRECTIONS_CONFIG_PATH,
            note=(
                "Built-in sample data uses the repository sample files shown in this "
                "workflow, so the downloaded CI workflow matches this dashboard analysis."
            ),
        )

    note = (
        "Uploaded files are analyzed in-memory. To use the downloaded CI workflow, save "
        "those files in your repository at the paths shown in the workflow, or edit the "
        "workflow paths."
    )
    if not has_directions_upload:
        return DashboardWorkflowContext(
            baseline_path=DASHBOARD_UPLOAD_BASELINE_PATH,
            current_path=DASHBOARD_UPLOAD_CURRENT_PATH,
            directions_config_path=None,
            note=(
                f"{note} No directions config was uploaded, so the generated workflow uses "
                "the fallback metric direction selected in the sidebar."
            ),
        )

    return DashboardWorkflowContext(
        baseline_path=DASHBOARD_UPLOAD_BASELINE_PATH,
        current_path=DASHBOARD_UPLOAD_CURRENT_PATH,
        directions_config_path=DASHBOARD_UPLOAD_DIRECTIONS_CONFIG_PATH,
        note=(
            f"{note} Save the uploaded directions config at "
            f"{DASHBOARD_UPLOAD_DIRECTIONS_CONFIG_PATH.as_posix()} or edit the workflow "
            "path to match your repository."
        ),
    )


def _format_threshold(threshold: float) -> str:
    if threshold.is_integer():
        return str(int(threshold))
    return str(threshold)


def _quote_path_arg(path: Path) -> str:
    path_value = path.as_posix()
    quoted_path = shlex.quote(path_value)
    if quoted_path == path_value:
        return f"'{quoted_path}'"
    return quoted_path


def generate_github_actions_workflow(
    *,
    baseline_path: Path = DEFAULT_BASELINE_PATH,
    current_path: Path = DEFAULT_CURRENT_PATH,
    directions_config_path: Path | None = DEFAULT_DIRECTIONS_CONFIG_PATH,
    threshold: float = DEFAULT_THRESHOLD,
    python_version: str = DEFAULT_PYTHON_VERSION,
    direction: MetricDirection = MetricDirection.HIGHER_IS_WORSE,
) -> str:
    """Generate a deterministic GitHub Actions workflow for benchmark guardrails."""
    threshold_value = _format_threshold(threshold)
    baseline_arg = _quote_path_arg(baseline_path)
    current_arg = _quote_path_arg(current_path)
    directions_config_line = (
        f"          --directions-config {_quote_path_arg(directions_config_path)}\n"
        if directions_config_path is not None
        else ""
    )
    markdown_report_arg = _quote_path_arg(DEFAULT_MARKDOWN_REPORT_PATH)
    html_report_arg = _quote_path_arg(DEFAULT_HTML_REPORT_PATH)
    codex_prompt_arg = _quote_path_arg(DEFAULT_CODEX_PROMPT_PATH)
    direction_value = direction.value
    return f"""name: Benchmark Guardian

on:
  push:
  pull_request:

jobs:
  benchmark-guardrail:
    runs-on: ubuntu-latest
    steps:
      - name: Check out repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: \"{python_version}\"

      - name: Install project
        run: pip install -e \".[dev]\"

      - name: Run benchmark regression guardrail
        run: >-
          cbg compare-files
          {baseline_arg}
          {current_arg}
          --threshold {threshold_value}
          --direction {direction_value}
{directions_config_line}          --report {markdown_report_arg}
          --html-report {html_report_arg}
          --codex-prompt {codex_prompt_arg}
          --fail-on-regression
"""


def write_github_actions_workflow(
    output_path: Path,
    *,
    baseline_path: Path = DEFAULT_BASELINE_PATH,
    current_path: Path = DEFAULT_CURRENT_PATH,
    directions_config_path: Path | None = DEFAULT_DIRECTIONS_CONFIG_PATH,
    threshold: float = DEFAULT_THRESHOLD,
    python_version: str = DEFAULT_PYTHON_VERSION,
    direction: MetricDirection = MetricDirection.HIGHER_IS_WORSE,
) -> str:
    """Write a benchmark guardrail workflow and return its contents."""
    workflow = generate_github_actions_workflow(
        baseline_path=baseline_path,
        current_path=current_path,
        directions_config_path=directions_config_path,
        threshold=threshold,
        python_version=python_version,
        direction=direction,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(workflow, encoding="utf-8")
    return workflow
