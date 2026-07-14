from pathlib import Path

from codex_benchmark_guardian.ci import generate_github_actions_workflow


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
    assert "examples/baseline.json" in workflow
    assert "examples/current_no_regression.json" in workflow
    assert "--directions-config examples/directions.json" in workflow
    assert "--report reports/report.md" in workflow
    assert "--html-report reports/report.html" in workflow


def test_generated_workflow_includes_fail_on_regression() -> None:
    workflow = generate_github_actions_workflow()

    assert "--fail-on-regression" in workflow


def test_generated_workflow_includes_codex_prompt() -> None:
    workflow = generate_github_actions_workflow()

    assert "--codex-prompt reports/codex_fix_prompt.md" in workflow


def test_generated_workflow_uses_custom_options() -> None:
    workflow = generate_github_actions_workflow(
        baseline_path=Path("benchmarks/base.json"),
        current_path=Path("benchmarks/new.json"),
        directions_config_path=Path("benchmarks/directions.json"),
        threshold=12.5,
        python_version="3.13",
    )

    assert 'python-version: "3.13"' in workflow
    assert "benchmarks/base.json" in workflow
    assert "benchmarks/new.json" in workflow
    assert "--directions-config benchmarks/directions.json" in workflow
    assert "--threshold 12.5" in workflow
