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


DEFAULT_PR_GATE_OUTPUT_PATH = Path(".github/workflows/benchmark-pr-gate.yml")


def generate_pr_gate_workflow() -> str:
    """Generate the protected, read-only PR benchmark gate workflow."""
    return """name: Benchmark PR Gate

# This definition intentionally runs from the protected base branch.
on:
  pull_request_target:
    types: [opened, synchronize, reopened]

permissions:
  contents: read

jobs:
  benchmark-protected-base:
    runs-on: ubuntu-latest
    permissions: {contents: read}
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.event.pull_request.base.sha }}
          path: source
          persist-credentials: false
      - run: |
          python -m venv .venv-base
          .venv-base/bin/python -m pip install ./source
          .venv-base/bin/python source/benchmarks/run_project_benchmarks.py --output reports/baseline.json --benchmark-mode full-pr-gate --workload-size 500 --iterations 7 --warmups 2 --operation-repetitions 50
      - uses: actions/upload-artifact@v4
        with: {name: codex-benchmark-baseline, path: reports/baseline.json, if-no-files-found: error}
  benchmark-pr-head:
    runs-on: ubuntu-latest
    permissions: {contents: read}
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.event.pull_request.base.sha }}
          path: protected-base
          persist-credentials: false
      - uses: actions/checkout@v4
        with:
          repository: ${{ github.event.pull_request.head.repo.full_name }}
          ref: ${{ github.event.pull_request.head.sha }}
          path: pr-head
          persist-credentials: false
      - run: |
          cp -R protected-base/benchmarks benchmark-harness
          python -m venv .venv-head
          .venv-head/bin/python -m pip install ./pr-head
          .venv-head/bin/python benchmark-harness/run_project_benchmarks.py --output reports/current.json --benchmark-mode full-pr-gate --workload-size 500 --iterations 7 --warmups 2 --operation-repetitions 50
      - uses: actions/upload-artifact@v4
        with: {name: codex-benchmark-current, path: reports/current.json, if-no-files-found: error}
  benchmark-pr-gate:
    needs: [benchmark-protected-base, benchmark-pr-head]
    if: always()
    runs-on: ubuntu-latest
    permissions: {contents: read}
    steps:
      - name: Fail on benchmark infrastructure failure
        if: needs.benchmark-protected-base.result != 'success' || needs.benchmark-pr-head.result != 'success'
        run: exit 1
      - uses: actions/checkout@v4
        if: needs.benchmark-protected-base.result == 'success' && needs.benchmark-pr-head.result == 'success'
        with:
          ref: ${{ github.event.pull_request.base.sha }}
          path: protected-base
          persist-credentials: false
      - uses: actions/download-artifact@v4
        with: {name: codex-benchmark-baseline, path: downloaded-baseline}
      - uses: actions/download-artifact@v4
        with: {name: codex-benchmark-current, path: downloaded-current}
      - run: |
          python -m venv .venv-evaluator
          .venv-evaluator/bin/python -m pip install ./protected-base
          .venv-evaluator/bin/cbg handoff-pack --baseline downloaded-baseline/baseline.json --current downloaded-current/current.json --directions-config protected-base/benchmarks/directions.json --threshold 25 --output-dir reports/handoff
          mkdir -p reports/benchmarks
          cp downloaded-baseline/baseline.json reports/benchmarks/baseline.json
          cp downloaded-current/current.json reports/benchmarks/current.json
      - name: Validate benchmarks and write provenance
        env:
          BASE_SHA: ${{ github.event.pull_request.base.sha }}
          HEAD_SHA: ${{ github.event.pull_request.head.sha }}
          PR_NUMBER: ${{ github.event.pull_request.number }}
        run: |
          python - <<'PY'
          import json
          import math
          import os
          from pathlib import Path
          baseline_path = Path("reports/benchmarks/baseline.json")
          current_path = Path("reports/benchmarks/current.json")
          directions_path = Path("protected-base/benchmarks/directions.json")
          for path in (baseline_path, current_path, directions_path):
              if not path.is_file() or path.stat().st_size > 1_000_000:
                  raise SystemExit(f"Invalid benchmark file: {path}")
          baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
          current = json.loads(current_path.read_text(encoding="utf-8"))
          directions = json.loads(directions_path.read_text(encoding="utf-8"))
          if not isinstance(baseline, dict) or not baseline or not isinstance(current, dict):
              raise SystemExit("Benchmark evidence must be non-empty objects")
          metric_names = sorted(baseline)
          valid = lambda value: isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
          if set(baseline) != set(current) or not set(baseline).issubset(directions) or not all(valid(value) for values in (baseline, current) for value in values.values()):
              raise SystemExit("Invalid benchmark evidence")
          provenance = {"pr_number": int(os.environ["PR_NUMBER"]), "base_sha": os.environ["BASE_SHA"], "head_sha": os.environ["HEAD_SHA"], "harness_source": "protected-base", "evaluator_source": "protected-base", "benchmark_mode": "full-pr-gate", "workload_size": 500, "operation_repetitions": 50, "iterations": 7, "warmups": 2, "threshold_percent": 25, "generated_metric_names": metric_names}
          Path("reports/benchmarks/provenance.json").write_text(json.dumps(provenance, indent=2) + chr(10), encoding="utf-8")
          PY
      - name: Add trusted gate summary
        run: |
          cat reports/handoff/pr_comment.md >> "$GITHUB_STEP_SUMMARY"
          echo "Harness: protected-base | Evaluator: protected-base | Benchmark mode: full-pr-gate | Threshold: 25%" >> "$GITHUB_STEP_SUMMARY"
      - uses: actions/upload-artifact@v4
        with:
          name: codex-benchmark-gate-evidence
          path: reports
          if-no-files-found: error
      - run: .venv-evaluator/bin/cbg enforce-gate reports/handoff/gate_summary.json
"""  # noqa: E501


def write_pr_gate_workflow(output_path: Path = DEFAULT_PR_GATE_OUTPUT_PATH) -> str:
    """Write the PR gate workflow and return its deterministic contents."""
    workflow = generate_pr_gate_workflow()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(workflow, encoding="utf-8")
    return workflow


DEFAULT_PR_GATE_PUBLISHER_OUTPUT_PATH = Path(".github/workflows/benchmark-pr-gate-publish.yml")


def generate_pr_gate_publisher_workflow() -> str:
    """Generate the trusted default-branch publisher workflow."""
    return """name: Benchmark PR Gate Publisher

on:
  workflow_run:
    workflows: ["Benchmark PR Gate"]
    types: [completed]

permissions:
  actions: read
  contents: read
  issues: write
  pull-requests: write

jobs:
  publish:
    if: github.event.workflow_run.event == 'pull_request_target'
    runs-on: ubuntu-latest
    steps:
      - name: Resolve eligible pull request
        id: resolve
        uses: actions/github-script@v9
        with:
          script: |
            const run = context.payload.workflow_run;
            const prs = Array.isArray(run.pull_requests) ? run.pull_requests : [];
            if (prs.length !== 1) {
              core.setOutput('should_publish', 'false');
              await core.summary.addRaw('Publisher skipped because the source workflow run did not contain exactly one associated pull request.').write();
              return;
            }
            const pr = await github.rest.pulls.get({ ...context.repo, pull_number: prs[0].number });
            const currentRepository = `${context.repo.owner}/${context.repo.repo}`;
            const baseRepository = pr.data.base.repo?.full_name;
            const headRepository = pr.data.head.repo?.full_name;
            if (baseRepository !== currentRepository) throw new Error('Source workflow run does not correspond to this repository');
            if (!headRepository || headRepository !== currentRepository) {
              core.setOutput('should_publish', 'false');
              await core.summary.addRaw('Publisher skipped because persistent benchmark comments are limited to same-repository pull requests.').write();
              return;
            }
            core.setOutput('should_publish', 'true');
            core.setOutput('pr_number', String(pr.data.number));
            core.setOutput('base_sha', String(pr.data.base.sha));
            core.setOutput('head_sha', String(pr.data.head.sha));
      - name: Download evidence from source run
        if: steps.resolve.outputs.should_publish == 'true'
        uses: actions/download-artifact@v4
        with:
          name: codex-benchmark-gate-evidence
          run-id: ${{ github.event.workflow_run.id }}
          github-token: ${{ secrets.GITHUB_TOKEN }}
          path: downloaded-evidence
      - name: Validate evidence and PR identity
        if: steps.resolve.outputs.should_publish == 'true'
        id: validate
        uses: actions/github-script@v9
        env:
          EXPECTED_BASE_SHA: ${{ steps.resolve.outputs.base_sha }}
          EXPECTED_HEAD_SHA: ${{ steps.resolve.outputs.head_sha }}
        with:
          script: |
            const fs = require('fs');
            const run = context.payload.workflow_run;
            const expectedBase = process.env.EXPECTED_BASE_SHA;
            const expectedHead = process.env.EXPECTED_HEAD_SHA;
            const root = 'downloaded-evidence/reports/benchmarks/';
            const provenance = JSON.parse(fs.readFileSync(root + 'provenance.json', 'utf8'));
            const required = ['base_sha', 'head_sha', 'harness_source', 'evaluator_source', 'benchmark_mode', 'threshold_percent', 'operation_repetitions', 'iterations'];
            if (!required.every(key => key in provenance) || provenance.head_sha !== expectedHead || provenance.base_sha !== expectedBase) throw new Error('Evidence provenance mismatch');
            if (provenance.harness_source !== 'protected-base' || provenance.evaluator_source !== 'protected-base' || provenance.benchmark_mode !== 'full-pr-gate' || provenance.threshold_percent !== 25 || !Number.isInteger(provenance.operation_repetitions) || provenance.operation_repetitions < 1 || provenance.operation_repetitions > 1000 || !Number.isInteger(provenance.iterations) || provenance.iterations < 1 || provenance.iterations > 100) throw new Error('Invalid evidence provenance');
            const baseline = JSON.parse(fs.readFileSync(root + 'baseline.json', 'utf8'));
            const current = JSON.parse(fs.readFileSync(root + 'current.json', 'utf8'));
            const valid = value => typeof value === 'number' && Number.isFinite(value);
            if (Object.keys(baseline).sort().join() !== Object.keys(current).sort().join() || !Object.values(baseline).every(valid) || !Object.values(current).every(valid)) throw new Error('Invalid benchmark evidence');
      - name: Check out validated protected base
        if: steps.resolve.outputs.should_publish == 'true'
        uses: actions/checkout@v4
        with:
          ref: ${{ steps.resolve.outputs.base_sha }}
          path: trusted-base
          persist-credentials: false
      - name: Regenerate trusted handoff comment
        if: steps.resolve.outputs.should_publish == 'true'
        run: |
          python -m venv .venv-publisher
          .venv-publisher/bin/python -m pip install ./trusted-base
          .venv-publisher/bin/cbg handoff-pack --baseline downloaded-evidence/reports/benchmarks/baseline.json --current downloaded-evidence/reports/benchmarks/current.json --directions-config trusted-base/benchmarks/directions.json --threshold 25 --output-dir trusted-handoff
      - name: Publish trusted persistent comment
        if: steps.resolve.outputs.should_publish == 'true'
        uses: actions/github-script@v9
        with:
          script: |
            const fs = require('fs');
            const marker = '<!-- codex-benchmark-guardian:pr-gate -->';
            const comment = fs.readFileSync('trusted-handoff/pr_comment.md', 'utf8').trim();
            const provenance = JSON.parse(fs.readFileSync('downloaded-evidence/reports/benchmarks/provenance.json', 'utf8'));
            const runUrl = `${process.env.GITHUB_SERVER_URL}/${process.env.GITHUB_REPOSITORY}/actions/runs/${context.payload.workflow_run.id}`;
            const details = `Base: ${provenance.base_sha.slice(0, 7)} | Head: ${provenance.head_sha.slice(0, 7)} | Harness: ${provenance.harness_source} | Evaluator: ${provenance.evaluator_source} | Benchmark mode: ${provenance.benchmark_mode} | Threshold: ${provenance.threshold_percent}%`;
            const body = [comment, details, `[View source workflow run](${runUrl})`].join(String.fromCharCode(10, 10));
            const issue_number = Number('${{ steps.resolve.outputs.pr_number }}');
            const comments = await github.paginate(github.rest.issues.listComments, { ...context.repo, issue_number });
            const existing = comments.find(item => item.body && item.body.includes(marker));
            if (existing) await github.rest.issues.updateComment({ ...context.repo, comment_id: existing.id, body });
            else await github.rest.issues.createComment({ ...context.repo, issue_number, body });
"""  # noqa: E501


def write_pr_gate_publisher_workflow(
    output_path: Path = DEFAULT_PR_GATE_PUBLISHER_OUTPUT_PATH,
) -> str:
    workflow = generate_pr_gate_publisher_workflow()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(workflow, encoding="utf-8")
    return workflow
