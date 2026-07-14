from __future__ import annotations

from collections.abc import Sequence

from codex_benchmark_guardian.regression import RegressionResult


def generate_markdown_report(results: Sequence[RegressionResult]) -> str:
    """Generate a Markdown benchmark comparison report."""
    regression_count = sum(result.is_regression for result in results)
    lines = [
        "# Benchmark Comparison Report",
        "",
        f"Compared metrics: {len(results)}",
        f"Regressions detected: {regression_count}",
        "",
        "| Metric | Baseline | Current | Change | Threshold | Status | Severity |",
        "| --- | ---: | ---: | ---: | ---: | --- | --- |",
    ]

    for result in results:
        status = "Regression" if result.is_regression else "OK"
        lines.append(
            "| "
            f"{result.metric_name} | "
            f"{result.baseline_value:g} | "
            f"{result.current_value:g} | "
            f"{result.change_percent:.2f}% | "
            f"{result.threshold_percent:.2f}% | "
            f"{status} | "
            f"{result.severity} |"
        )

    lines.append("")
    return "\n".join(lines)
