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
    assert "Benchmark Release Readiness" in report
    assert "Score:</strong> 70/100" in report
    assert "Benchmark regressions require review before merging." in report
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
    assert "## Benchmark Release Readiness" in report
    assert "**Score:** 70/100" in report


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


def test_generate_codex_fix_prompt_with_regressions() -> None:
    from codex_benchmark_guardian.report import generate_codex_fix_prompt

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
        ),
    ]

    prompt = generate_codex_fix_prompt(results)

    assert "# Codex Benchmark Guardian" in prompt
    assert "Benchmark regressions were detected" in prompt
    assert "Total compared metrics: 2" in prompt
    assert "Regressions detected: 1" in prompt
    assert "| latency_ms | higher_is_worse | 100 | 125 | 25.00% | high |" in prompt
    assert "memory_mb" not in prompt
    assert "Request path latency or dependency wait time" in prompt
    assert "Inspect this repository" in prompt
    assert "Release readiness: Needs Review (70/100)" in prompt


def test_generate_codex_fix_prompt_without_regressions() -> None:
    from codex_benchmark_guardian.report import generate_codex_fix_prompt

    results = [
        RegressionResult(
            metric_name="latency_ms",
            baseline_value=100.0,
            current_value=105.0,
            change_percent=5.0,
            threshold_percent=10.0,
            is_regression=False,
            severity="none",
        )
    ]

    prompt = generate_codex_fix_prompt(results)

    assert "Regressions detected: 0" in prompt
    assert "No benchmark regressions were detected" in prompt
    assert "no regression fix is needed" in prompt
    assert "Review benchmark stability" in prompt


def test_generate_codex_fix_prompt_includes_quality_checks() -> None:
    from codex_benchmark_guardian.report import generate_codex_fix_prompt

    prompt = generate_codex_fix_prompt([])

    assert "`make lint`" in prompt
    assert "`make format-check`" in prompt
    assert "`make test`" in prompt
    assert "`make demo-ci`" in prompt


def test_generate_github_issue_with_regressions() -> None:
    from codex_benchmark_guardian.report import generate_github_issue

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

    issue = generate_github_issue(results)

    assert "# Benchmark regression handoff" in issue
    assert "Investigate 1 benchmark regression" in issue
    assert "Compared metrics count: 1" in issue
    assert "Regression count: 1" in issue
    assert "| latency_ms | higher_is_worse | 100 | 125 | 25.00% | 10.00% | high |" in issue
    assert "Request path latency or dependency wait time" in issue
    assert "Suggested Codex Task" in issue
    assert "Release readiness score: 70/100" in issue


def test_generate_github_issue_without_regressions() -> None:
    from codex_benchmark_guardian.report import generate_github_issue

    results = [
        RegressionResult(
            metric_name="latency_ms",
            baseline_value=100.0,
            current_value=105.0,
            change_percent=5.0,
            threshold_percent=10.0,
            is_regression=False,
            severity="none",
        )
    ]

    issue = generate_github_issue(results)

    assert "No benchmark regression issue needed" in issue
    assert "No regression issue is needed" in issue
    assert "monitoring benchmark stability" in issue
    assert "Regression count: 0" in issue
    assert "| latency_ms |" not in issue


def test_generate_github_issue_includes_quality_checks() -> None:
    from codex_benchmark_guardian.report import generate_github_issue

    issue = generate_github_issue([])

    assert "`make lint`" in issue
    assert "`make format-check`" in issue
    assert "`make test`" in issue
    assert "`make demo-ci`" in issue
