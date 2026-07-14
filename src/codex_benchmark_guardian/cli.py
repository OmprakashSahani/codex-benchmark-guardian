from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from codex_benchmark_guardian.benchmarks import compare_benchmark_metrics, load_benchmark_file
from codex_benchmark_guardian.regression import detect_regression
from codex_benchmark_guardian.report import generate_markdown_report

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
    threshold: float = typer.Option(
        10.0,
        "--threshold",
        "-t",
        help="Regression threshold percentage.",
    ),
) -> None:
    """Compare a baseline benchmark value against a current value."""
    result = detect_regression(
        metric_name=metric_name,
        baseline_value=baseline_value,
        current_value=current_value,
        threshold_percent=threshold,
    )

    console.print(f"[bold]Metric:[/bold] {result.metric_name}")
    console.print(f"[bold]Baseline:[/bold] {result.baseline_value}")
    console.print(f"[bold]Current:[/bold] {result.current_value}")
    console.print(f"[bold]Change:[/bold] {result.change_percent:.2f}%")
    console.print(f"[bold]Threshold:[/bold] {result.threshold_percent:.2f}%")

    if result.is_regression:
        console.print(f"[red]Regression detected[/red] | Severity: {result.severity}")
    else:
        console.print("[green]No regression detected[/green]")


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
) -> None:
    """Compare benchmark metrics from two JSON files and write a Markdown report."""
    baseline_metrics = load_benchmark_file(baseline_path)
    current_metrics = load_benchmark_file(current_path)
    results = compare_benchmark_metrics(
        baseline_metrics=baseline_metrics,
        current_metrics=current_metrics,
        threshold_percent=threshold,
    )

    if not results:
        raise typer.BadParameter("no matching numeric metrics found")

    report = generate_markdown_report(results)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")

    regression_count = sum(result.is_regression for result in results)
    console.print(f"Compared {len(results)} metrics")
    console.print(f"Regressions detected: {regression_count}")
    console.print(f"Report written to: {report_path}")


if __name__ == "__main__":
    app()
