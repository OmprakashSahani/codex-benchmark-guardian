from __future__ import annotations

from collections.abc import Sequence
from html import escape

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
        "| Metric | Direction | Baseline | Current | Change | Threshold | Status | Severity |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- | --- |",
    ]

    for result in results:
        status = "Regression" if result.is_regression else "OK"
        lines.append(
            "| "
            f"{result.metric_name} | "
            f"{result.direction.value} | "
            f"{result.baseline_value:g} | "
            f"{result.current_value:g} | "
            f"{result.change_percent:.2f}% | "
            f"{result.threshold_percent:.2f}% | "
            f"{status} | "
            f"{result.severity} |"
        )

    lines.append("")
    return "\n".join(lines)


def generate_html_report(results: Sequence[RegressionResult]) -> str:
    """Generate a self-contained HTML benchmark comparison report."""
    regression_count = sum(result.is_regression for result in results)
    rows = []

    for result in results:
        status = "Regression" if result.is_regression else "OK"
        status_class = "regression" if result.is_regression else "ok"
        rows.append(
            "        <tr>\n"
            f"          <td>{escape(result.metric_name)}</td>\n"
            f"          <td>{escape(result.direction.value)}</td>\n"
            f"          <td>{result.baseline_value:g}</td>\n"
            f"          <td>{result.current_value:g}</td>\n"
            f"          <td>{result.change_percent:.2f}%</td>\n"
            f"          <td>{result.threshold_percent:.2f}%</td>\n"
            f'          <td class="{status_class}">{status}</td>\n'
            f"          <td>{escape(result.severity)}</td>\n"
            "        </tr>"
        )

    table_rows = "\n".join(rows)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Codex Benchmark Guardian Report</title>
  <style>
    body {{
      color: #172033;
      font-family: Arial, sans-serif;
      line-height: 1.5;
      margin: 2rem auto;
      max-width: 960px;
      padding: 0 1rem;
    }}
    h1 {{ margin-bottom: 0.25rem; }}
    .summary {{
      background: #f5f7fb;
      border: 1px solid #d9e0ee;
      border-radius: 8px;
      margin: 1.5rem 0;
      padding: 1rem;
    }}
    table {{
      border-collapse: collapse;
      width: 100%;
    }}
    th,
    td {{
      border: 1px solid #d9e0ee;
      padding: 0.6rem;
      text-align: left;
    }}
    th {{ background: #edf2fb; }}
    .regression {{ color: #b42318; font-weight: bold; }}
    .ok {{ color: #027a48; font-weight: bold; }}
  </style>
</head>
<body>
  <h1>Codex Benchmark Guardian</h1>
  <section class="summary" aria-labelledby="summary-heading">
    <h2 id="summary-heading">Summary</h2>
    <p>Total compared metrics: {len(results)}</p>
    <p>Regressions detected: {regression_count}</p>
  </section>
  <table>
    <thead>
      <tr>
        <th>Metric</th>
        <th>Direction</th>
        <th>Baseline</th>
        <th>Current</th>
        <th>Change Percent</th>
        <th>Threshold</th>
        <th>Status</th>
        <th>Severity</th>
      </tr>
    </thead>
    <tbody>
{table_rows}
    </tbody>
  </table>
</body>
</html>
"""
