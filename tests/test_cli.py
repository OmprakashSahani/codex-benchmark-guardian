import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from codex_benchmark_guardian.cli import app

runner = CliRunner()


def test_about_command() -> None:
    result = runner.invoke(app, ["about"])

    assert result.exit_code == 0
    assert "Codex Benchmark Guardian" in result.output
    assert "testing" in result.output
    assert "benchmarking" in result.output
    assert "reliability reporting" in result.output


def test_version_command() -> None:
    result = runner.invoke(app, ["version"])

    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_compare_command_detects_regression() -> None:
    result = runner.invoke(
        app,
        ["compare", "latency_ms", "100", "125", "--threshold", "10"],
    )

    assert result.exit_code == 0
    assert "Metric:" in result.output
    assert "latency_ms" in result.output
    assert "Change:" in result.output
    assert "25.00%" in result.output
    assert "Regression detected" in result.output
    assert "high" in result.output


def test_compare_command_no_regression() -> None:
    result = runner.invoke(
        app,
        ["compare", "latency_ms", "100", "105", "--threshold", "10"],
    )

    assert result.exit_code == 0
    assert "No regression detected" in result.output


def test_compare_command_detects_lower_is_worse_regression() -> None:
    result = runner.invoke(
        app,
        [
            "compare",
            "throughput_rps",
            "1000",
            "850",
            "--threshold",
            "10",
            "--direction",
            "lower_is_worse",
        ],
    )

    assert result.exit_code == 0
    assert "throughput_rps" in result.output
    assert "-15.00%" in result.output
    assert "lower_is_worse" in result.output
    assert "Regression detected" in result.output


def test_compare_files_command_creates_report(tmp_path) -> None:
    baseline_path = tmp_path / "baseline.json"
    current_path = tmp_path / "current.json"
    report_path = tmp_path / "reports" / "report.md"
    baseline_path.write_text(
        json.dumps({"latency_ms": 100.0, "memory_mb": 256.0, "runtime_s": 2.5}),
        encoding="utf-8",
    )
    current_path.write_text(
        json.dumps({"latency_ms": 125.0, "memory_mb": 260.0, "runtime_s": 2.7}),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "compare-files",
            str(baseline_path),
            str(current_path),
            "--threshold",
            "10",
            "--report",
            str(report_path),
        ],
    )

    assert result.exit_code == 0
    assert "Compared 3 metrics" in result.output
    assert "Regressions detected: 1" in result.output
    assert "Report written to:" in result.output
    assert report_path.exists()
    report = report_path.read_text(encoding="utf-8")
    assert "# Benchmark Comparison Report" in report
    assert (
        "| latency_ms | higher_is_worse | 100 | 125 | 25.00% | 10.00% | Regression | high |"
    ) in report
    assert ("| memory_mb | higher_is_worse | 256 | 260 | 1.56% | 10.00% | OK | none |") in report
    assert ("| runtime_s | higher_is_worse | 2.5 | 2.7 | 8.00% | 10.00% | OK | none |") in report


def test_compare_files_command_creates_html_report(tmp_path) -> None:
    baseline_path = tmp_path / "baseline.json"
    current_path = tmp_path / "current.json"
    report_path = tmp_path / "reports" / "report.md"
    html_report_path = tmp_path / "reports" / "report.html"
    baseline_path.write_text(
        json.dumps({"latency_ms": 100.0, "memory_mb": 256.0}),
        encoding="utf-8",
    )
    current_path.write_text(
        json.dumps({"latency_ms": 125.0, "memory_mb": 260.0}),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "compare-files",
            str(baseline_path),
            str(current_path),
            "--threshold",
            "10",
            "--report",
            str(report_path),
            "--html-report",
            str(html_report_path),
        ],
    )

    assert result.exit_code == 0
    assert "Compared 2 metrics" in result.output
    assert "Regressions detected: 1" in result.output
    assert "Report written to:" in result.output
    assert "HTML report written to:" in result.output
    assert report_path.exists()
    assert html_report_path.exists()
    html_report = html_report_path.read_text(encoding="utf-8")
    assert "Codex Benchmark Guardian" in html_report
    assert "Total compared metrics: 2" in html_report
    assert "Regressions detected: 1" in html_report
    assert '<td class="regression">Regression</td>' in html_report
    assert '<td class="ok">OK</td>' in html_report


def test_compare_files_without_fail_on_regression_exits_zero_for_regressions(
    tmp_path,
) -> None:
    baseline_path = tmp_path / "baseline.json"
    current_path = tmp_path / "current.json"
    report_path = tmp_path / "reports" / "report.md"
    baseline_path.write_text(json.dumps({"latency_ms": 100.0}), encoding="utf-8")
    current_path.write_text(json.dumps({"latency_ms": 125.0}), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "compare-files",
            str(baseline_path),
            str(current_path),
            "--threshold",
            "10",
            "--report",
            str(report_path),
        ],
    )

    assert result.exit_code == 0
    assert "Regressions detected: 1" in result.output
    assert report_path.exists()


def test_compare_files_with_fail_on_regression_exits_non_zero_for_regressions(
    tmp_path,
) -> None:
    baseline_path = tmp_path / "baseline.json"
    current_path = tmp_path / "current.json"
    report_path = tmp_path / "reports" / "report.md"
    baseline_path.write_text(json.dumps({"latency_ms": 100.0}), encoding="utf-8")
    current_path.write_text(json.dumps({"latency_ms": 125.0}), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "compare-files",
            str(baseline_path),
            str(current_path),
            "--threshold",
            "10",
            "--report",
            str(report_path),
            "--fail-on-regression",
        ],
    )

    assert result.exit_code == 1
    assert "Regressions detected: 1" in result.output
    assert "Failing because 1 benchmark regression(s) were detected." in result.output
    assert report_path.exists()


def test_compare_files_with_fail_on_regression_exits_zero_without_regressions(
    tmp_path,
) -> None:
    baseline_path = tmp_path / "baseline.json"
    current_path = tmp_path / "current.json"
    report_path = tmp_path / "reports" / "report.md"
    baseline_path.write_text(json.dumps({"latency_ms": 100.0}), encoding="utf-8")
    current_path.write_text(json.dumps({"latency_ms": 105.0}), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "compare-files",
            str(baseline_path),
            str(current_path),
            "--threshold",
            "10",
            "--report",
            str(report_path),
            "--fail-on-regression",
        ],
    )

    assert result.exit_code == 0
    assert "Regressions detected: 0" in result.output
    assert "Failing because" not in result.output
    assert report_path.exists()


def test_compare_files_command_with_lower_is_worse_direction(tmp_path) -> None:
    baseline_path = tmp_path / "baseline.json"
    current_path = tmp_path / "current.json"
    report_path = tmp_path / "reports" / "report.md"
    html_report_path = tmp_path / "reports" / "report.html"
    baseline_path.write_text(json.dumps({"throughput_rps": 1000.0}), encoding="utf-8")
    current_path.write_text(json.dumps({"throughput_rps": 850.0}), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "compare-files",
            str(baseline_path),
            str(current_path),
            "--threshold",
            "10",
            "--direction",
            "lower_is_worse",
            "--report",
            str(report_path),
            "--html-report",
            str(html_report_path),
        ],
    )

    assert result.exit_code == 0
    assert "Regressions detected: 1" in result.output
    assert "lower_is_worse" in report_path.read_text(encoding="utf-8")
    html_report = html_report_path.read_text(encoding="utf-8")
    assert "<th>Direction</th>" in html_report
    assert "<td>lower_is_worse</td>" in html_report


def test_compare_files_command_with_directions_config(tmp_path) -> None:
    baseline_path = tmp_path / "baseline.json"
    current_path = tmp_path / "current.json"
    directions_path = tmp_path / "directions.json"
    report_path = tmp_path / "reports" / "report.md"
    baseline_path.write_text(
        json.dumps({"latency_ms": 100.0, "throughput_rps": 1000.0}),
        encoding="utf-8",
    )
    current_path.write_text(
        json.dumps({"latency_ms": 125.0, "throughput_rps": 850.0}),
        encoding="utf-8",
    )
    directions_path.write_text(
        json.dumps({"throughput_rps": "lower_is_worse"}),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "compare-files",
            str(baseline_path),
            str(current_path),
            "--threshold",
            "10",
            "--directions-config",
            str(directions_path),
            "--report",
            str(report_path),
        ],
    )

    assert result.exit_code == 0
    assert "Regressions detected: 2" in result.output
    report = report_path.read_text(encoding="utf-8")
    assert (
        "| latency_ms | higher_is_worse | 100 | 125 | 25.00% | 10.00% | Regression | high |"
    ) in report
    assert (
        "| throughput_rps | lower_is_worse | 1000 | 850 | -15.00% | 10.00% | Regression | medium |"
    ) in report


def test_compare_files_command_rejects_invalid_directions_config(tmp_path) -> None:
    baseline_path = tmp_path / "baseline.json"
    current_path = tmp_path / "current.json"
    directions_path = tmp_path / "directions.json"
    report_path = tmp_path / "reports" / "report.md"
    baseline_path.write_text(json.dumps({"latency_ms": 100.0}), encoding="utf-8")
    current_path.write_text(json.dumps({"latency_ms": 125.0}), encoding="utf-8")
    directions_path.write_text(
        json.dumps({"latency_ms": "sideways_is_worse"}),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "compare-files",
            str(baseline_path),
            str(current_path),
            "--directions-config",
            str(directions_path),
            "--report",
            str(report_path),
        ],
    )

    assert result.exit_code != 0
    assert "invalid direction for latency_ms" in result.output
    assert not report_path.exists()


def test_compare_files_command_creates_codex_prompt(tmp_path) -> None:
    baseline_path = tmp_path / "baseline.json"
    current_path = tmp_path / "current.json"
    report_path = tmp_path / "reports" / "report.md"
    codex_prompt_path = tmp_path / "reports" / "codex_fix_prompt.md"
    baseline_path.write_text(json.dumps({"latency_ms": 100.0}), encoding="utf-8")
    current_path.write_text(json.dumps({"latency_ms": 125.0}), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "compare-files",
            str(baseline_path),
            str(current_path),
            "--threshold",
            "10",
            "--report",
            str(report_path),
            "--codex-prompt",
            str(codex_prompt_path),
        ],
    )

    assert result.exit_code == 0
    assert "Codex fix prompt written to:" in result.output
    assert codex_prompt_path.exists()
    prompt = codex_prompt_path.read_text(encoding="utf-8")
    assert "| latency_ms | higher_is_worse | 100 | 125 | 25.00% | high |" in prompt
    assert "Regression Triage Guidance" in prompt
    assert "Request path latency or dependency wait time" in prompt


def test_init_ci_command_creates_output_file_and_parent_dirs(tmp_path) -> None:
    output_path = tmp_path / "nested" / "reports" / "benchmark_guardian_ci.yml"

    result = runner.invoke(app, ["init-ci", "--output", str(output_path)])

    assert result.exit_code == 0
    assert "CI guardrail workflow written to:" in result.output
    assert output_path.exists()
    workflow = output_path.read_text(encoding="utf-8")
    assert "cbg compare-files" in workflow
    assert "--fail-on-regression" in workflow
    assert "--codex-prompt 'reports/codex_fix_prompt.md'" in workflow


def test_init_ci_command_uses_default_github_actions_output(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["init-ci"], catch_exceptions=False, env={})

    assert result.exit_code == 0
    assert (
        "CI guardrail workflow written to: .github/workflows/benchmark-guardian.yml"
        in result.output
    )
    default_output = Path(".github/workflows/benchmark-guardian.yml")
    assert default_output.exists()


@pytest.mark.parametrize(
    ("baseline_path", "current_path"),
    [
        ("examples/baseline.json", "examples/current.json"),
        ("./examples/baseline.json", "./examples/current.json"),
        (
            str(Path("examples/baseline.json").resolve()),
            str(Path("examples/current.json").resolve()),
        ),
    ],
)
def test_handoff_pack_command_bundled_sample_paths_use_bundled_directions_config(
    tmp_path,
    baseline_path,
    current_path,
) -> None:
    output_dir = tmp_path / "handoff"

    result = runner.invoke(
        app,
        [
            "handoff-pack",
            "--baseline",
            baseline_path,
            "--current",
            current_path,
            "--threshold",
            "10",
            "--output-dir",
            str(output_dir),
        ],
    )

    assert result.exit_code == 0
    assert "FileNotFoundError" not in result.output
    report = (output_dir / "report.md").read_text(encoding="utf-8")
    assert (
        "| throughput_rps | lower_is_worse | 1000 | 850 | -15.00% | 10.00% | Regression | medium |"
        in report
    )
    workflow = (output_dir / "benchmark_guardian_ci.yml").read_text(encoding="utf-8")
    assert "--directions-config 'examples/directions.json'" in workflow


def test_handoff_pack_command_defaults_to_bundled_directions_config(tmp_path) -> None:
    output_dir = tmp_path / "handoff"

    result = runner.invoke(
        app,
        [
            "handoff-pack",
            "--threshold",
            "10",
            "--output-dir",
            str(output_dir),
        ],
    )

    assert result.exit_code == 0
    report = (output_dir / "report.md").read_text(encoding="utf-8")
    assert (
        "| throughput_rps | lower_is_worse | 1000 | 850 | -15.00% | 10.00% | Regression | medium |"
        in report
    )


def test_handoff_pack_command_explicit_directions_config_overrides_default(
    tmp_path,
) -> None:
    directions_path = tmp_path / "directions.json"
    output_dir = tmp_path / "handoff"
    directions_path.write_text(
        json.dumps({"throughput_rps": "higher_is_worse"}),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "handoff-pack",
            "--directions-config",
            str(directions_path),
            "--threshold",
            "10",
            "--output-dir",
            str(output_dir),
        ],
    )

    assert result.exit_code == 0
    report = (output_dir / "report.md").read_text(encoding="utf-8")
    assert (
        "| throughput_rps | higher_is_worse | 1000 | 850 | -15.00% | 10.00% | OK | none |" in report
    )
    workflow = (output_dir / "benchmark_guardian_ci.yml").read_text(encoding="utf-8")
    assert f"--directions-config '{directions_path}'" in workflow


def test_handoff_pack_command_creates_all_expected_files(tmp_path) -> None:
    baseline_path = tmp_path / "baseline.json"
    current_path = tmp_path / "current.json"
    directions_path = tmp_path / "directions.json"
    output_dir = tmp_path / "reports" / "handoff"
    baseline_path.write_text(
        json.dumps({"latency_ms": 100.0, "throughput_rps": 1000.0}),
        encoding="utf-8",
    )
    current_path.write_text(
        json.dumps({"latency_ms": 125.0, "throughput_rps": 850.0}),
        encoding="utf-8",
    )
    directions_path.write_text(
        json.dumps({"throughput_rps": "lower_is_worse"}),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "handoff-pack",
            "--baseline",
            str(baseline_path),
            "--current",
            str(current_path),
            "--directions-config",
            str(directions_path),
            "--threshold",
            "10",
            "--output-dir",
            str(output_dir),
        ],
    )

    assert result.exit_code == 0
    assert "Codex Handoff Pack written to:" in result.output
    expected_files = {
        "report.md",
        "report.html",
        "codex_fix_prompt.md",
        "github_issue.md",
        "benchmark_guardian_ci.yml",
    }
    assert {path.name for path in output_dir.iterdir()} == expected_files
    issue = (output_dir / "github_issue.md").read_text(encoding="utf-8")
    assert "| latency_ms | higher_is_worse | 100 | 125 | 25.00% | 10.00% | high |" in issue
    assert "| throughput_rps | lower_is_worse | 1000 | 850 | -15.00% | 10.00% | medium |" in issue
    assert "`make lint`" in issue
    assert "`make format-check`" in issue
    assert "`make test`" in issue
    assert "`make demo-ci`" in issue


def test_handoff_pack_command_works_without_directions_config(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    baseline_path = tmp_path / "base.json"
    current_path = tmp_path / "current.json"
    output_dir = tmp_path / "handoff"
    baseline_path.write_text(json.dumps({"latency_ms": 100.0}), encoding="utf-8")
    current_path.write_text(json.dumps({"latency_ms": 125.0}), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "handoff-pack",
            "--baseline",
            str(baseline_path),
            "--current",
            str(current_path),
            "--output-dir",
            str(output_dir),
        ],
    )

    assert result.exit_code == 0
    assert "Codex Handoff Pack written to:" in result.output
    assert (output_dir / "report.md").exists()
    workflow = (output_dir / "benchmark_guardian_ci.yml").read_text(encoding="utf-8")
    assert "--directions-config" not in workflow


def test_handoff_pack_command_custom_inputs_do_not_trigger_bundled_directions_config(
    tmp_path,
) -> None:
    baseline_path = tmp_path / "baseline.json"
    current_path = tmp_path / "current.json"
    output_dir = tmp_path / "handoff"
    baseline_path.write_text(json.dumps({"throughput_rps": 1000.0}), encoding="utf-8")
    current_path.write_text(json.dumps({"throughput_rps": 850.0}), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "handoff-pack",
            "--baseline",
            str(baseline_path),
            "--current",
            str(current_path),
            "--threshold",
            "10",
            "--output-dir",
            str(output_dir),
        ],
    )

    assert result.exit_code == 0
    report = (output_dir / "report.md").read_text(encoding="utf-8")
    assert (
        "| throughput_rps | higher_is_worse | 1000 | 850 | -15.00% | 10.00% | OK | none |" in report
    )
    workflow = (output_dir / "benchmark_guardian_ci.yml").read_text(encoding="utf-8")
    assert "--directions-config" not in workflow


def test_handoff_pack_command_custom_inputs_without_directions_config_use_fallback_direction(
    tmp_path,
) -> None:
    baseline_path = tmp_path / "base.json"
    current_path = tmp_path / "current.json"
    output_dir = tmp_path / "handoff"
    baseline_path.write_text(json.dumps({"throughput_rps": 1000.0}), encoding="utf-8")
    current_path.write_text(json.dumps({"throughput_rps": 850.0}), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "handoff-pack",
            "--baseline",
            str(baseline_path),
            "--current",
            str(current_path),
            "--direction",
            "lower_is_worse",
            "--threshold",
            "10",
            "--output-dir",
            str(output_dir),
        ],
    )

    assert result.exit_code == 0
    assert "FileNotFoundError" not in result.output
    report = (output_dir / "report.md").read_text(encoding="utf-8")
    assert (
        "| throughput_rps | lower_is_worse | 1000 | 850 | -15.00% | 10.00% | Regression | medium |"
        in report
    )


def test_demo_handoff_explicitly_passes_directions_config() -> None:
    makefile = Path("Makefile").read_text(encoding="utf-8")

    assert "cbg handoff-pack" in makefile
    assert "--directions-config examples/directions.json" in makefile
