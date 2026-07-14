from __future__ import annotations

import typer
from rich.console import Console

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


if __name__ == "__main__":
    app()
