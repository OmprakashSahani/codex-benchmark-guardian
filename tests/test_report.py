from codex_benchmark_guardian.regression import MetricDirection, RegressionResult
from codex_benchmark_guardian.report import generate_html_report, generate_markdown_report


def test_generate_html_report() -> None:
    results = [
        RegressionResult(
            metric_name="latency_ms",
            baseline_value=100.0,
            current_value=125.0,
            change_percent=25.0,
            threshold_percent=10.0,
            is_regression=True,
            severity="high",
        ),
        RegressionResult(
            metric_name="memory_mb",
            baseline_value=256.0,
            current_value=260.0,
            change_percent=1.5625,
            threshold_percent=10.0,
            is_regression=False,
            severity="none",
            direction=MetricDirection.LOWER_IS_WORSE,
        ),
    ]

    report = generate_html_report(results)

    assert "<!doctype html>" in report
    assert "<h1>Codex Benchmark Guardian</h1>" in report
    assert '<h2 id="summary-heading">Summary</h2>' in report
    assert "Total compared metrics: 2" in report
    assert "Regressions detected: 1" in report
    assert "<th>Direction</th>" in report
    assert "<th>Change Percent</th>" in report
    assert "<td>latency_ms</td>" in report
    assert "<td>higher_is_worse</td>" in report
    assert "<td>lower_is_worse</td>" in report
    assert '<td class="regression">Regression</td>' in report
    assert '<td class="ok">OK</td>' in report


def test_generate_markdown_report_includes_triage_section() -> None:
    results = [
        RegressionResult(
            metric_name="latency_ms",
            baseline_value=100.0,
            current_value=125.0,
            change_percent=25.0,
            threshold_percent=10.0,
            is_regression=True,
            severity="high",
        )
    ]

    report = generate_markdown_report(results)

    assert "## Regression Triage" in report
    assert "### latency_ms" in report
    assert "**Likely area:** Request path latency or dependency wait time" in report
    assert "**Suggested checks:**" in report


def test_generate_html_report_includes_triage_section() -> None:
    results = [
        RegressionResult(
            metric_name="throughput_rps",
            baseline_value=1000.0,
            current_value=850.0,
            change_percent=-15.0,
            threshold_percent=10.0,
            is_regression=True,
            severity="medium",
            direction=MetricDirection.LOWER_IS_WORSE,
        )
    ]

    report = generate_html_report(results)

    assert '<section class="triage" aria-labelledby="triage-heading">' in report
    assert '<h2 id="triage-heading">Regression Triage</h2>' in report
    assert "throughput_rps" in report
    assert "Capacity, concurrency, or request processing rate" in report
