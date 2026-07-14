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
