import json

from typer.testing import CliRunner

from codex_benchmark_guardian.cli import app
from codex_benchmark_guardian.pr_gate import (
    PR_COMMENT_MARKER,
    build_pr_gate_summary,
    generate_gate_summary_json,
    generate_pr_comment,
)
from codex_benchmark_guardian.regression import MetricDirection, RegressionResult

runner = CliRunner()


def result(name: str, severity: str = "none", regression: bool = False) -> RegressionResult:
    return RegressionResult(
        name, 100, 125, 25, 10, regression, severity, MetricDirection.HIGHER_IS_WORSE
    )


def test_gate_summaries_reuse_readiness_and_are_deterministic() -> None:
    block = build_pr_gate_summary(
        [result("latency_ms", "high", True), result("throughput_rps", "medium", True)]
    )
    ready = build_pr_gate_summary([result("latency_ms")])
    review = build_pr_gate_summary(
        [result("latency_ms", "medium", True), result("memory_mb", "low", True)]
    )
    assert (block.readiness_score, block.readiness_label, block.should_block) == (50, "Block", True)
    assert (ready.readiness_score, ready.readiness_label) == (100, "Ready")
    assert (review.readiness_score, review.readiness_label) == (70, "Needs Review")
    assert json.loads(generate_gate_summary_json(block))["recommendation"] == block.recommendation
    assert generate_gate_summary_json(block) == generate_gate_summary_json(block)


def test_comments_include_marker_regressions_and_escape_tables() -> None:
    comment = generate_pr_comment([result("latency|ms", "high", True)])
    assert comment.startswith(PR_COMMENT_MARKER)
    assert "| latency\\|ms |" in comment
    assert "Regression Triage Advisor" in comment
    assert "make format-check" in comment


def test_ready_comment_is_concise_success() -> None:
    comment = generate_pr_comment([result("latency_ms")])
    assert "Benchmark gate passed" in comment
    assert "Regressed metrics" not in comment


def test_enforce_gate_exit_codes_and_invalid_json(tmp_path) -> None:
    for name, payload, code in (
        (
            "ready",
            {
                "compared_metrics": 1,
                "regression_count": 0,
                "readiness_score": 100,
                "readiness_label": "Ready",
                "recommendation": "ok",
                "should_block": False,
            },
            0,
        ),
        (
            "review",
            {
                "compared_metrics": 1,
                "regression_count": 1,
                "readiness_score": 70,
                "readiness_label": "Needs Review",
                "recommendation": "review",
                "should_block": False,
            },
            0,
        ),
        (
            "block",
            {
                "compared_metrics": 1,
                "regression_count": 1,
                "readiness_score": 50,
                "readiness_label": "Block",
                "recommendation": "block",
                "should_block": True,
            },
            1,
        ),
    ):
        path = tmp_path / f"{name}.json"
        path.write_text(json.dumps(payload))
        assert runner.invoke(app, ["enforce-gate", str(path)]).exit_code == code
    bad = tmp_path / "bad.json"
    bad.write_text("{")
    assert runner.invoke(app, ["enforce-gate", str(bad)]).exit_code != 0
