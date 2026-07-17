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
    """Generate the base-versus-head pull-request benchmark gate workflow."""
    return """name: Benchmark PR Gate

on:
  pull_request:
    types: [opened, synchronize, reopened]

permissions:
  contents: read

concurrency:
  group: benchmark-pr-gate-${{ github.event.pull_request.number }}
  cancel-in-progress: true

jobs:
  benchmark-pr-gate:
    runs-on: ubuntu-latest
    steps:
      - name: Check out PR head
        uses: actions/checkout@v4
        with:
          ref: ${{ github.event.pull_request.head.sha }}
          path: current-src
          persist-credentials: false
      - name: Check out protected base
        uses: actions/checkout@v4
        with:
          ref: ${{ github.event.pull_request.base.sha }}
          path: baseline-src
          persist-credentials: false
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Select protected benchmark harness
        run: |
          mkdir -p benchmark-harness reports/benchmarks
          if [ -f baseline-src/benchmarks/run_project_benchmarks.py ] && [ -f baseline-src/src/codex_benchmark_guardian/pr_gate.py ] && [ -f baseline-src/src/codex_benchmark_guardian/handoff.py ]; then
            cp baseline-src/benchmarks/run_project_benchmarks.py benchmark-harness/
            cp baseline-src/benchmarks/directions.json benchmark-harness/
            echo "HARNESS_SOURCE=protected-base" >> "$GITHUB_ENV"
            echo "BENCHMARK_MODE=full-pr-gate" >> "$GITHUB_ENV"
            echo "BASE_EVALUATOR_SUPPORTED=true" >> "$GITHUB_ENV"
          else
            cp current-src/benchmarks/run_project_benchmarks.py benchmark-harness/
            cp current-src/benchmarks/directions.json benchmark-harness/
            echo "HARNESS_SOURCE=bootstrap-current" >> "$GITHUB_ENV"
            echo "BENCHMARK_MODE=bootstrap-common" >> "$GITHUB_ENV"
            echo "BASE_EVALUATOR_SUPPORTED=false" >> "$GITHUB_ENV"
          fi
      - name: Create isolated benchmark environments
        run: |
          python -m venv .venv-baseline
          python -m venv .venv-current
          .venv-baseline/bin/python -m pip install --upgrade pip
          .venv-current/bin/python -m pip install --upgrade pip
          .venv-baseline/bin/python -m pip install ./baseline-src
          .venv-current/bin/python -m pip install ./current-src
      - name: Select protected gate evaluator
        run: |
          if [ "$BASE_EVALUATOR_SUPPORTED" = "true" ]; then
            "$GITHUB_WORKSPACE/.venv-baseline/bin/cbg" --help | grep -q handoff-pack
            "$GITHUB_WORKSPACE/.venv-baseline/bin/cbg" --help | grep -q enforce-gate
            echo "EVALUATOR_SOURCE=protected-base" >> "$GITHUB_ENV"
            echo "EVALUATOR_CBG=$GITHUB_WORKSPACE/.venv-baseline/bin/cbg" >> "$GITHUB_ENV"
          else
            echo "EVALUATOR_SOURCE=bootstrap-current" >> "$GITHUB_ENV"
            echo "EVALUATOR_CBG=$GITHUB_WORKSPACE/.venv-current/bin/cbg" >> "$GITHUB_ENV"
          fi
      - name: Benchmark protected base
        run: >-
          .venv-baseline/bin/python benchmark-harness/run_project_benchmarks.py
          --output reports/benchmarks/baseline.json --workload-size 500 --iterations 7 --warmups 2 --benchmark-mode "$BENCHMARK_MODE" --operation-repetitions 50
      - name: Benchmark PR head
        run: >-
          .venv-current/bin/python benchmark-harness/run_project_benchmarks.py
          --output reports/benchmarks/current.json --workload-size 500 --iterations 7 --warmups 2 --benchmark-mode "$BENCHMARK_MODE" --operation-repetitions 50
      - name: Write benchmark provenance
        env:
          BASE_SHA: ${{ github.event.pull_request.base.sha }}
          HEAD_SHA: ${{ github.event.pull_request.head.sha }}
        run: |
          python -c 'import json, os; from pathlib import Path; directions=json.loads(Path("benchmark-harness/directions.json").read_text()); Path("reports/benchmarks/provenance.json").write_text(json.dumps({"base_sha": os.environ["BASE_SHA"], "head_sha": os.environ["HEAD_SHA"], "harness_source": os.environ["HARNESS_SOURCE"], "evaluator_source": os.environ["EVALUATOR_SOURCE"], "benchmark_mode": os.environ["BENCHMARK_MODE"], "workload_size": 500, "operation_repetitions": 50, "iterations": 7, "warmups": 2, "threshold_percent": 25, "generated_metric_names": sorted(directions)}, indent=2, sort_keys=True) + "\\n")'
      - name: Build Codex Handoff Pack
        run: >-
          "$EVALUATOR_CBG" handoff-pack --baseline reports/benchmarks/baseline.json
          --current reports/benchmarks/current.json --directions-config benchmark-harness/directions.json
          --threshold 25 --output-dir reports/handoff
      - name: Upload benchmark gate evidence
        uses: actions/upload-artifact@v4
        with:
          name: codex-benchmark-gate-evidence
          path: |
            reports/benchmarks/baseline.json
            reports/benchmarks/current.json
            reports/benchmarks/provenance.json
            reports/handoff
          if-no-files-found: error
      - name: Add gate comment and provenance to job summary
        env:
          BASE_SHA: ${{ github.event.pull_request.base.sha }}
          HEAD_SHA: ${{ github.event.pull_request.head.sha }}
        run: |
          cat reports/handoff/pr_comment.md >> "$GITHUB_STEP_SUMMARY"
          printf '\\nBase: %.7s | Head: %.7s | Harness: %s | Mode: %s | Threshold: 25%%\\n' "$BASE_SHA" "$HEAD_SHA" "$HARNESS_SOURCE" "$BENCHMARK_MODE" >> "$GITHUB_STEP_SUMMARY"
      - name: Explain trusted comment publication
        run: echo "Persistent PR comment publication is handled by the trusted Benchmark PR Gate Publisher workflow." >> "$GITHUB_STEP_SUMMARY"
      - name: Enforce stored release readiness
        run: '"$EVALUATOR_CBG" enforce-gate reports/handoff/gate_summary.json'
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
    if: >-
      github.event.workflow_run.event == 'pull_request' &&
      github.event.workflow_run.head_repository.full_name == github.repository &&
      github.event.workflow_run.pull_requests.size == 1
    runs-on: ubuntu-latest
    steps:
      - name: Download evidence from source run
        uses: actions/download-artifact@v4
        with:
          name: codex-benchmark-gate-evidence
          run-id: ${{ github.event.workflow_run.id }}
          github-token: ${{ secrets.GITHUB_TOKEN }}
          path: downloaded-evidence
      - name: Validate evidence and PR identity
        id: validate
        uses: actions/github-script@v9
        with:
          script: |
            const fs = require('fs');
            const run = context.payload.workflow_run;
            const prs = run.pull_requests;
            if (prs.length !== 1) throw new Error('Expected one associated pull request');
            const pr = await github.rest.pulls.get({ ...context.repo, pull_number: prs[0].number });
            const root = 'downloaded-evidence/reports/benchmarks/';
            const provenance = JSON.parse(fs.readFileSync(root + 'provenance.json', 'utf8'));
            const required = ['base_sha', 'head_sha', 'harness_source', 'evaluator_source', 'benchmark_mode', 'threshold_percent', 'operation_repetitions', 'iterations'];
            if (!required.every(key => key in provenance) || provenance.head_sha !== run.head_sha || provenance.base_sha !== pr.data.base.sha) throw new Error('Evidence provenance mismatch');
            if (!['protected-base', 'bootstrap-current'].includes(provenance.harness_source) || !['protected-base', 'bootstrap-current'].includes(provenance.evaluator_source) || !['full-pr-gate', 'bootstrap-common'].includes(provenance.benchmark_mode) || provenance.threshold_percent !== 25 || !Number.isInteger(provenance.operation_repetitions) || provenance.operation_repetitions < 1 || provenance.operation_repetitions > 1000 || !Number.isInteger(provenance.iterations) || provenance.iterations < 1 || provenance.iterations > 100) throw new Error('Invalid evidence provenance');
            const baseline = JSON.parse(fs.readFileSync(root + 'baseline.json', 'utf8'));
            const current = JSON.parse(fs.readFileSync(root + 'current.json', 'utf8'));
            const valid = value => typeof value === 'number' && Number.isFinite(value);
            if (Object.keys(baseline).sort().join() !== Object.keys(current).sort().join() || !Object.values(baseline).every(valid) || !Object.values(current).every(valid)) throw new Error('Invalid benchmark evidence');
            core.setOutput('base_sha', pr.data.base.sha);
            core.setOutput('pr_number', String(pr.data.number));
      - name: Check out validated protected base
        uses: actions/checkout@v4
        with:
          ref: ${{ steps.validate.outputs.base_sha }}
          path: trusted-base
          persist-credentials: false
      - name: Regenerate trusted handoff comment
        run: |
          python -m venv .venv-publisher
          .venv-publisher/bin/python -m pip install ./trusted-base
          .venv-publisher/bin/cbg handoff-pack --baseline downloaded-evidence/reports/benchmarks/baseline.json --current downloaded-evidence/reports/benchmarks/current.json --directions-config trusted-base/benchmarks/directions.json --threshold 25 --output-dir trusted-handoff
      - name: Publish trusted persistent comment
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
            const issue_number = Number('${{ steps.validate.outputs.pr_number }}');
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
