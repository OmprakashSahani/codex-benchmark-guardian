import json

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
    assert "| latency_ms | 100 | 125 | 25.00% | 10.00% | Regression | high |" in report
    assert "| memory_mb | 256 | 260 | 1.56% | 10.00% | OK | none |" in report
    assert "| runtime_s | 2.5 | 2.7 | 8.00% | 10.00% | OK | none |" in report


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
