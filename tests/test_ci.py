from pathlib import Path

from codex_benchmark_guardian.ci import (
    DEFAULT_OUTPUT_PATH,
    generate_github_actions_workflow,
    select_dashboard_workflow_context,
)
from codex_benchmark_guardian.regression import MetricDirection


def test_default_output_path_is_github_actions_workflow() -> None:
    assert DEFAULT_OUTPUT_PATH == Path(".github/workflows/benchmark-guardian.yml")


def test_generated_workflow_contains_github_actions_structure() -> None:
    workflow = generate_github_actions_workflow()

    assert "name: Benchmark Guardian" in workflow
    assert "on:\n  push:\n  pull_request:" in workflow
    assert "runs-on: ubuntu-latest" in workflow
    assert "uses: actions/checkout@v4" in workflow
    assert "uses: actions/setup-python@v5" in workflow
    assert 'python-version: "3.12"' in workflow
    assert 'run: pip install -e ".[dev]"' in workflow


def test_generated_workflow_includes_compare_files() -> None:
    workflow = generate_github_actions_workflow()

    assert "cbg compare-files" in workflow
    assert "'examples/baseline.json'" in workflow
    assert "'examples/current_no_regression.json'" in workflow
    assert "--directions-config 'examples/directions.json'" in workflow
    assert "--report 'reports/report.md'" in workflow
    assert "--html-report 'reports/report.html'" in workflow


def test_generated_workflow_includes_fail_on_regression() -> None:
    workflow = generate_github_actions_workflow()

    assert "--fail-on-regression" in workflow


def test_generated_workflow_includes_codex_prompt() -> None:
    workflow = generate_github_actions_workflow()

    assert "--codex-prompt 'reports/codex_fix_prompt.md'" in workflow


def test_generated_workflow_uses_custom_options() -> None:
    workflow = generate_github_actions_workflow(
        baseline_path=Path("benchmarks/base.json"),
        current_path=Path("benchmarks/new.json"),
        directions_config_path=Path("benchmarks/directions.json"),
        threshold=12.5,
        python_version="3.13",
    )

    assert 'python-version: "3.13"' in workflow
    assert "'benchmarks/base.json'" in workflow
    assert "'benchmarks/new.json'" in workflow
    assert "--directions-config 'benchmarks/directions.json'" in workflow
    assert "--threshold 12.5" in workflow


def test_generated_workflow_handles_custom_paths_with_spaces() -> None:
    workflow = generate_github_actions_workflow(
        baseline_path=Path("benchmark data/baseline.json"),
        current_path=Path("benchmark data/current.json"),
        directions_config_path=Path("benchmark data/directions.json"),
    )

    assert "'benchmark data/baseline.json'" in workflow
    assert "'benchmark data/current.json'" in workflow
    assert "--directions-config 'benchmark data/directions.json'" in workflow


def test_dashboard_sample_workflow_context_uses_regressing_examples() -> None:
    context = select_dashboard_workflow_context(
        use_sample_data=True,
        has_directions_upload=False,
    )

    assert context.baseline_path == Path("examples/baseline.json")
    assert context.current_path == Path("examples/current.json")
    assert context.directions_config_path == Path("examples/directions.json")
    assert "matches this dashboard analysis" in context.note


def test_dashboard_sample_workflow_includes_directions_config() -> None:
    context = select_dashboard_workflow_context(
        use_sample_data=True,
        has_directions_upload=False,
    )

    workflow = generate_github_actions_workflow(
        baseline_path=context.baseline_path,
        current_path=context.current_path,
        directions_config_path=context.directions_config_path,
    )

    assert "--directions-config 'examples/directions.json'" in workflow


def test_dashboard_upload_workflow_context_uses_placeholder_repo_paths() -> None:
    context = select_dashboard_workflow_context(
        use_sample_data=False,
        has_directions_upload=True,
    )

    assert context.baseline_path == Path("benchmarks/baseline.json")
    assert context.current_path == Path("benchmarks/current.json")
    assert context.directions_config_path == Path("benchmarks/directions.json")
    assert "Uploaded files are analyzed in-memory" in context.note
    assert "Save the uploaded directions config at benchmarks/directions.json" in context.note
    assert "No directions config was uploaded" not in context.note


def test_dashboard_upload_workflow_with_directions_upload_includes_directions_config() -> None:
    context = select_dashboard_workflow_context(
        use_sample_data=False,
        has_directions_upload=True,
    )

    workflow = generate_github_actions_workflow(
        baseline_path=context.baseline_path,
        current_path=context.current_path,
        directions_config_path=context.directions_config_path,
    )

    assert "--directions-config 'benchmarks/directions.json'" in workflow


def test_dashboard_upload_workflow_context_notes_missing_directions_upload() -> None:
    context = select_dashboard_workflow_context(
        use_sample_data=False,
        has_directions_upload=False,
    )

    assert context.directions_config_path is None
    assert (
        "No directions config was uploaded, so the generated workflow uses the fallback "
        "metric direction selected in the sidebar."
    ) in context.note


def test_dashboard_upload_workflow_without_directions_upload_omits_directions_config() -> None:
    context = select_dashboard_workflow_context(
        use_sample_data=False,
        has_directions_upload=False,
    )

    workflow = generate_github_actions_workflow(
        baseline_path=context.baseline_path,
        current_path=context.current_path,
        directions_config_path=context.directions_config_path,
    )

    assert "--directions-config" not in workflow


def test_dashboard_upload_workflow_without_directions_upload_keeps_direction_fallback() -> None:
    context = select_dashboard_workflow_context(
        use_sample_data=False,
        has_directions_upload=False,
    )

    workflow = generate_github_actions_workflow(
        baseline_path=context.baseline_path,
        current_path=context.current_path,
        directions_config_path=context.directions_config_path,
        direction=MetricDirection.LOWER_IS_WORSE,
    )

    assert "--direction lower_is_worse" in workflow


def test_generated_workflow_uses_custom_direction() -> None:
    workflow = generate_github_actions_workflow(direction=MetricDirection.LOWER_IS_WORSE)

    assert "--direction lower_is_worse" in workflow


def test_pr_gate_workflow_is_safe_and_orders_artifact_before_enforcement() -> None:
    from codex_benchmark_guardian.ci import generate_pr_gate_workflow

    workflow = generate_pr_gate_workflow()
    assert "pull_request_target" not in workflow
    assert "actions/upload-artifact@v4" in workflow
    assert "actions/github-script@v9" in workflow
    assert "contents: read" in workflow and "pull-requests: write" in workflow
    assert "head.repo.full_name == github.repository" in workflow
    assert "codex-benchmark-guardian:pr-gate" in workflow
    assert workflow.index("actions/upload-artifact@v4") < workflow.index("cbg enforce-gate")
