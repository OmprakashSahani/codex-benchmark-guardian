from __future__ import annotations

import typer
from rich.console import Console

from codex_benchmark_guardian.regression import detect_regression

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


if __name__ == "__main__":
    app()
