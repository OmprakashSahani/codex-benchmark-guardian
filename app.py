from __future__ import annotations

import json
from typing import Any

import streamlit as st

from codex_benchmark_guardian.benchmarks import (
    compare_benchmark_metrics,
    parse_benchmark_metrics,
    parse_directions_config,
)
from codex_benchmark_guardian.ci import (
    generate_github_actions_workflow,
    select_dashboard_workflow_context,
)
from codex_benchmark_guardian.regression import MetricDirection
from codex_benchmark_guardian.release_readiness import (
    calculate_release_readiness,
    generate_release_readiness_markdown,
)
from codex_benchmark_guardian.report import (
    generate_codex_fix_prompt,
    generate_github_issue,
    generate_html_report,
    generate_markdown_report,
)
from codex_benchmark_guardian.triage import generate_triage_notes

SAMPLE_BASELINE = {
    "latency_ms": 100.0,
    "memory_mb": 256.0,
    "runtime_s": 2.5,
    "throughput_rps": 1000.0,
}
SAMPLE_CURRENT = {
    "latency_ms": 125.0,
    "memory_mb": 260.0,
    "runtime_s": 2.7,
    "throughput_rps": 850.0,
}
SAMPLE_DIRECTIONS = {
    "latency_ms": MetricDirection.HIGHER_IS_WORSE,
    "memory_mb": MetricDirection.HIGHER_IS_WORSE,
    "runtime_s": MetricDirection.HIGHER_IS_WORSE,
    "throughput_rps": MetricDirection.LOWER_IS_WORSE,
}


def _load_uploaded_json(uploaded_file: Any) -> Any:
    if uploaded_file is None:
        return None
    return json.loads(uploaded_file.getvalue().decode("utf-8"))


def _results_table(results: list[Any]) -> list[dict[str, str | float]]:
    return [
        {
            "metric name": result.metric_name,
            "direction": result.direction.value,
            "baseline": result.baseline_value,
            "current": result.current_value,
            "change percent": f"{result.change_percent:.2f}%",
            "threshold": f"{result.threshold_percent:.2f}%",
            "status": "Regression" if result.is_regression else "OK",
            "severity": result.severity,
        }
        for result in results
    ]


st.set_page_config(page_title="Codex Benchmark Guardian", page_icon="🛡️", layout="wide")

st.title("Codex Benchmark Guardian")
st.write(
    "Upload baseline and current benchmark JSON files, configure a regression threshold, "
    "and run the same comparison engine used by the CLI to produce triage guidance, "
    "Codex fix prompts, reports, and CI guardrails."
)

with st.sidebar:
    st.header("Analysis controls")
    threshold = st.number_input(
        "Regression threshold (%)",
        min_value=0.0,
        value=10.0,
        step=1.0,
        help=(
            "A metric is a regression when it moves in the worse direction "
            "by at least this percent."
        ),
    )
    fallback_direction = st.selectbox(
        "Fallback metric direction",
        options=[direction.value for direction in MetricDirection],
        index=0,
        help="Used for metrics not listed in the directions config.",
    )
    use_sample_data = st.checkbox("Use built-in sample data", value=True)

st.subheader("Benchmark inputs")
col1, col2, col3 = st.columns(3)
with col1:
    baseline_upload = st.file_uploader("Baseline JSON", type="json")
with col2:
    current_upload = st.file_uploader("Current JSON", type="json")
with col3:
    directions_upload = st.file_uploader("Directions config JSON", type="json")

run_analysis = st.button("Run Analysis", type="primary")

if run_analysis:
    try:
        if use_sample_data:
            baseline_metrics = SAMPLE_BASELINE
            current_metrics = SAMPLE_CURRENT
            directions = SAMPLE_DIRECTIONS
        else:
            if baseline_upload is None or current_upload is None:
                st.error(
                    "Upload both baseline and current benchmark JSON files, or use sample data."
                )
                st.stop()
            baseline_metrics = parse_benchmark_metrics(_load_uploaded_json(baseline_upload))
            current_metrics = parse_benchmark_metrics(_load_uploaded_json(current_upload))
            directions_data = _load_uploaded_json(directions_upload)
            directions = (
                parse_directions_config(directions_data) if directions_data is not None else None
            )

        results = compare_benchmark_metrics(
            baseline_metrics=baseline_metrics,
            current_metrics=current_metrics,
            threshold_percent=threshold,
            direction=MetricDirection(fallback_direction),
            directions=directions,
        )
        if not results:
            st.warning(
                "No matching numeric metrics were found between the baseline and current inputs."
            )
            st.stop()

        regression_count = sum(result.is_regression for result in results)
        release_readiness = calculate_release_readiness(results)
        release_readiness_markdown = generate_release_readiness_markdown(results)
        markdown_report = generate_markdown_report(results)
        html_report = generate_html_report(results)
        codex_prompt = generate_codex_fix_prompt(results)
        workflow_context = select_dashboard_workflow_context(
            use_sample_data=use_sample_data,
            has_directions_upload=directions_upload is not None,
        )
        github_issue = generate_github_issue(results)
        ci_workflow = generate_github_actions_workflow(
            baseline_path=workflow_context.baseline_path,
            current_path=workflow_context.current_path,
            directions_config_path=workflow_context.directions_config_path,
            threshold=threshold,
            direction=MetricDirection(fallback_direction),
        )

        metric_col, regression_col = st.columns(2)
        metric_col.metric("Total compared metrics", len(results))
        regression_col.metric("Regressions detected", regression_count)

        st.subheader("Benchmark Release Readiness")
        readiness_col, score_col = st.columns(2)
        readiness_col.metric("Readiness", release_readiness.label.value)
        score_col.metric("Score", f"{release_readiness.score}/100")
        st.write(f"**Recommendation:** {release_readiness.recommendation}")

        st.subheader("Metric comparison")
        st.dataframe(_results_table(results), use_container_width=True, hide_index=True)

        triage_notes = generate_triage_notes(results)
        st.subheader("Regression Triage Advisor")
        if triage_notes:
            for note in triage_notes:
                with st.container(border=True):
                    st.markdown(f"**{note.metric_name}**")
                    st.write(f"**Likely area:** {note.likely_area}")
                    st.write(f"**Why it matters:** {note.why_it_matters}")
                    st.write("**Suggested checks:**")
                    for check in note.suggested_checks:
                        st.markdown(f"- {check}")
        else:
            st.success("No regressions detected. No triage guidance is needed.")

        with st.expander("Generated Codex Fix Prompt"):
            st.code(codex_prompt, language="markdown")

        with st.expander("Codex Handoff Pack"):
            st.write(
                "The report, Codex prompt, GitHub issue template, and CI workflow form "
                "a complete handoff workflow from regression detection to fixing and "
                "guardrail setup."
            )
            st.code(github_issue, language="markdown")
            st.download_button(
                "Download github_issue.md",
                github_issue,
                file_name="github_issue.md",
                mime="text/markdown",
            )

        with st.expander("Generated CI Guardrail Workflow YAML"):
            st.info(workflow_context.note)
            st.code(ci_workflow, language="yaml")

        st.subheader("Downloads")
        download_cols = st.columns(6)
        download_cols[0].download_button(
            "Markdown report",
            markdown_report,
            file_name="benchmark_report.md",
            mime="text/markdown",
        )
        download_cols[1].download_button(
            "HTML report",
            html_report,
            file_name="benchmark_report.html",
            mime="text/html",
        )
        download_cols[2].download_button(
            "Codex fix prompt",
            codex_prompt,
            file_name="codex_fix_prompt.md",
            mime="text/markdown",
        )
        download_cols[3].download_button(
            "GitHub issue",
            github_issue,
            file_name="github_issue.md",
            mime="text/markdown",
        )
        download_cols[4].download_button(
            "CI guardrail YAML",
            ci_workflow,
            file_name="benchmark-guardian.yml",
            mime="text/yaml",
        )
        download_cols[5].download_button(
            "Release readiness",
            release_readiness_markdown,
            file_name="release_readiness.md",
            mime="text/markdown",
        )
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
        st.error(f"Could not run analysis: {exc}")
