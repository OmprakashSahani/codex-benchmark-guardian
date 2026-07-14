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
