from __future__ import annotations

from collections.abc import Sequence
from html import escape

from codex_benchmark_guardian.regression import RegressionResult
from codex_benchmark_guardian.triage import generate_triage_notes


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

    triage_notes = generate_triage_notes(results)
    if triage_notes:
        lines.extend(["", "## Regression Triage", ""])
        for note in triage_notes:
            lines.extend(
                [
                    f"### {note.metric_name}",
                    "",
                    f"- **Likely area:** {note.likely_area}",
                    f"- **Why it matters:** {note.why_it_matters}",
                    "- **Suggested checks:**",
                ]
            )
            lines.extend(f"  - {check}" for check in note.suggested_checks)
            lines.append("")

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
    triage_notes = generate_triage_notes(results)
    triage_section = ""
    if triage_notes:
        triage_items = []
        for note in triage_notes:
            checks = "\n".join(
                f"          <li>{escape(check)}</li>" for check in note.suggested_checks
            )
            triage_items.append(
                '      <article class="triage-note">\n'
                f"        <h3>{escape(note.metric_name)}</h3>\n"
                f"        <p><strong>Likely area:</strong> {escape(note.likely_area)}</p>\n"
                f"        <p><strong>Why it matters:</strong> {escape(note.why_it_matters)}</p>\n"
                "        <p><strong>Suggested checks:</strong></p>\n"
                "        <ul>\n"
                f"{checks}\n"
                "        </ul>\n"
                "      </article>"
            )
        triage_section = (
            '  <section class="triage" aria-labelledby="triage-heading">\n'
            '    <h2 id="triage-heading">Regression Triage</h2>\n'
            f"{chr(10).join(triage_items)}\n"
            "  </section>\n"
        )

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
    .triage {{
      background: #fff8eb;
      border: 1px solid #f3d08a;
      border-radius: 8px;
      margin: 1.5rem 0;
      padding: 1rem;
    }}
    .triage-note {{ margin-top: 1rem; }}
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
{triage_section}</body>
</html>
"""
