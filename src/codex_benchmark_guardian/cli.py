from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from codex_benchmark_guardian.benchmarks import (
    compare_benchmark_metrics,
    load_benchmark_file,
    load_directions_config,
)
from codex_benchmark_guardian.ci import (
    DEFAULT_BASELINE_PATH,
    DEFAULT_CURRENT_PATH,
    DEFAULT_DIRECTIONS_CONFIG_PATH,
    DEFAULT_OUTPUT_PATH,
    DEFAULT_PYTHON_VERSION,
    DEFAULT_THRESHOLD,
    write_github_actions_workflow,
)
from codex_benchmark_guardian.regression import MetricDirection, detect_regression
from codex_benchmark_guardian.report import (
    generate_codex_fix_prompt,
    generate_html_report,
    generate_markdown_report,
)

app = typer.Typer(
    name="cbg",
    help=(
        "Codex Benchmark Guardian: detect performance regressions and improve software reliability."
    ),
    no_args_is_help=True,
)

console = Console()


@app.callback()
def main() -> None:
    """Codex Benchmark Guardian CLI."""
    return None


@app.command()
def about() -> None:
    """Show project information."""
    console.print("[bold]Codex Benchmark Guardian[/bold]")
    console.print(
        "A developer tool for testing, benchmarking, regression detection, "
        "and software reliability reporting."
    )


@app.command()
def version() -> None:
    """Show project version."""
    console.print("0.1.0")


@app.command()
def compare(
    metric_name: str,
    baseline_value: float,
    current_value: float,
    threshold: Annotated[
        float,
        typer.Option(
            "--threshold",
            "-t",
            help="Regression threshold percentage.",
        ),
    ] = 10.0,
    direction: Annotated[
        MetricDirection,
        typer.Option(
            "--direction",
            help="Metric direction that determines which movement is worse.",
        ),
    ] = MetricDirection.HIGHER_IS_WORSE,
) -> None:
    """Compare a baseline benchmark value against a current value."""
    result = detect_regression(
        metric_name=metric_name,
        baseline_value=baseline_value,
        current_value=current_value,
        threshold_percent=threshold,
        direction=direction,
    )

    console.print(f"[bold]Metric:[/bold] {result.metric_name}")
    console.print(f"[bold]Baseline:[/bold] {result.baseline_value}")
    console.print(f"[bold]Current:[/bold] {result.current_value}")
    console.print(f"[bold]Change:[/bold] {result.change_percent:.2f}%")
    console.print(f"[bold]Threshold:[/bold] {result.threshold_percent:.2f}%")
    console.print(f"[bold]Direction:[/bold] {result.direction.value}")

    if result.is_regression:
        console.print(f"[red]Regression detected[/red] | Severity: {result.severity}")
    else:
        console.print("[green]No regression detected[/green]")


@app.command("init-ci")
def init_ci(
    baseline_path: Annotated[
        Path,
        typer.Option(
            "--baseline",
            help="Path to the baseline benchmark JSON file used by the workflow.",
        ),
    ] = DEFAULT_BASELINE_PATH,
    current_path: Annotated[
        Path,
        typer.Option(
            "--current",
            help="Path to the current benchmark JSON file used by the workflow.",
        ),
    ] = DEFAULT_CURRENT_PATH,
    directions_config_path: Annotated[
        Path,
        typer.Option(
            "--directions-config",
            help="Path to the per-metric directions JSON file used by the workflow.",
        ),
    ] = DEFAULT_DIRECTIONS_CONFIG_PATH,
    threshold: Annotated[
        float,
        typer.Option(
            "--threshold",
            "-t",
            help="Regression threshold percentage used by the workflow.",
        ),
    ] = DEFAULT_THRESHOLD,
    python_version: Annotated[
        str,
        typer.Option(
            "--python-version",
            help="Python version configured for actions/setup-python.",
        ),
    ] = DEFAULT_PYTHON_VERSION,
    output_path: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            help="Path where the GitHub Actions workflow YAML should be written.",
        ),
    ] = DEFAULT_OUTPUT_PATH,
) -> None:
    """Generate a GitHub Actions benchmark regression guardrail workflow."""
    write_github_actions_workflow(
        output_path=output_path,
        baseline_path=baseline_path,
        current_path=current_path,
        directions_config_path=directions_config_path,
        threshold=threshold,
        python_version=python_version,
    )
    console.print(f"CI guardrail workflow written to: {output_path}")


@app.command("compare-files")
def compare_files(
    baseline_path: Annotated[
        Path,
        typer.Argument(
            help="Path to the baseline benchmark JSON file.",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
        ),
    ],
    current_path: Annotated[
        Path,
        typer.Argument(
            help="Path to the current benchmark JSON file.",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
        ),
    ],
    threshold: Annotated[
        float,
        typer.Option(
            "--threshold",
            "-t",
            help="Regression threshold percentage.",
        ),
    ] = 10.0,
    report_path: Annotated[
        Path,
        typer.Option(
            "--report",
            "-r",
            help="Path where the Markdown report should be written.",
        ),
    ] = ...,
    html_report_path: Annotated[
        Path | None,
        typer.Option(
            "--html-report",
            help="Optional path where the HTML report should be written.",
        ),
    ] = None,
    codex_prompt_path: Annotated[
        Path | None,
        typer.Option(
            "--codex-prompt",
            help="Optional path where a Codex regression-fix prompt should be written.",
        ),
    ] = None,
    direction: Annotated[
        MetricDirection,
        typer.Option(
            "--direction",
            help="Fallback metric direction for metrics not in --directions-config.",
        ),
    ] = MetricDirection.HIGHER_IS_WORSE,
    directions_config_path: Annotated[
        Path | None,
        typer.Option(
            "--directions-config",
            help="Optional JSON file mapping metric names to directions.",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
        ),
    ] = None,
    fail_on_regression: Annotated[
        bool,
        typer.Option(
            "--fail-on-regression",
            help="Exit with a non-zero status code when regressions are detected.",
        ),
    ] = False,
) -> None:
    """Compare benchmark metrics from two JSON files and write reports."""
    baseline_metrics = load_benchmark_file(baseline_path)
    current_metrics = load_benchmark_file(current_path)
    try:
        directions = (
            load_directions_config(directions_config_path)
            if directions_config_path is not None
            else None
        )
    except ValueError as exc:
        raise typer.BadParameter(str(exc), param_hint="--directions-config") from exc
    results = compare_benchmark_metrics(
        baseline_metrics=baseline_metrics,
        current_metrics=current_metrics,
        threshold_percent=threshold,
        direction=direction,
        directions=directions,
    )

    if not results:
        raise typer.BadParameter("no matching numeric metrics found")

    report = generate_markdown_report(results)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")

    if html_report_path is not None:
        html_report = generate_html_report(results)
        html_report_path.parent.mkdir(parents=True, exist_ok=True)
        html_report_path.write_text(html_report, encoding="utf-8")

    if codex_prompt_path is not None:
        codex_prompt = generate_codex_fix_prompt(results)
        codex_prompt_path.parent.mkdir(parents=True, exist_ok=True)
        codex_prompt_path.write_text(codex_prompt, encoding="utf-8")

    regression_count = sum(result.is_regression for result in results)
    console.print(f"Compared {len(results)} metrics")
    console.print(f"Regressions detected: {regression_count}")
    console.print(f"Report written to: {report_path}")
    if html_report_path is not None:
        console.print(f"HTML report written to: {html_report_path}")
    if codex_prompt_path is not None:
        console.print(f"Codex fix prompt written to: {codex_prompt_path}")

    if fail_on_regression and regression_count > 0:
        console.print(
            f"[red]Failing because {regression_count} benchmark regression(s) were detected.[/red]"
        )
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
