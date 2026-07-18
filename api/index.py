from __future__ import annotations

from typing import Annotated, Literal

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator

from codex_benchmark_guardian.benchmarks import compare_benchmark_metrics
from codex_benchmark_guardian.ci import (
    generate_github_actions_workflow,
    select_dashboard_workflow_context,
)
from codex_benchmark_guardian.pr_gate import build_pr_gate_summary
from codex_benchmark_guardian.regression import MetricDirection
from codex_benchmark_guardian.release_readiness import generate_release_readiness_markdown
from codex_benchmark_guardian.report import (
    generate_codex_fix_prompt,
    generate_github_issue,
    generate_html_report,
    generate_markdown_report,
)
from codex_benchmark_guardian.triage import generate_triage_notes

MAX_METRICS = 250
DirectionValue = Literal["higher_is_worse", "lower_is_worse"]
FiniteNumber = Annotated[float, Field(strict=True, allow_inf_nan=False)]


class AnalyzeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    baseline: dict[str, FiniteNumber]
    current: dict[str, FiniteNumber]
    threshold_percent: FiniteNumber = Field(default=10.0, ge=0, le=10000)
    fallback_direction: DirectionValue = "higher_is_worse"
    directions: dict[str, DirectionValue] | None = None
    use_sample_data: bool = False

    @field_validator("baseline", "current")
    @classmethod
    def validate_metrics(cls, metrics: dict[str, float]) -> dict[str, float]:
        if not metrics:
            raise ValueError("must contain at least one metric")
        if len(metrics) > MAX_METRICS:
            raise ValueError(f"must contain at most {MAX_METRICS} metrics")
        if any(not name.strip() for name in metrics):
            raise ValueError("metric names must not be empty")
        return metrics

    @field_validator("directions")
    @classmethod
    def validate_direction_count(
        cls, directions: dict[str, DirectionValue] | None
    ) -> dict[str, DirectionValue] | None:
        if directions is not None and len(directions) > MAX_METRICS:
            raise ValueError(f"must contain at most {MAX_METRICS} metrics")
        return directions


app = FastAPI(title="Codex Benchmark Guardian API", version="1.0.0")


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = []
    for error in exc.errors():
        location = ".".join(str(part) for part in error["loc"] if part != "body") or "body"
        errors.append({"field": location, "message": error["msg"]})
    return JSONResponse(
        status_code=422,
        content={"error": "Invalid analysis request", "details": errors},
    )


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/analyze")
async def analyze(payload: AnalyzeRequest) -> dict[str, object]:
    matching_metrics = payload.baseline.keys() & payload.current.keys()
    if not matching_metrics:
        return JSONResponse(
            status_code=422,
            content={
                "error": "Invalid analysis request",
                "details": [{"field": "baseline,current", "message": "no matching metrics"}],
            },
        )
    if any(payload.baseline[name] == 0 for name in matching_metrics):
        return JSONResponse(
            status_code=422,
            content={
                "error": "Invalid analysis request",
                "details": [
                    {
                        "field": "baseline",
                        "message": "matching baseline metric values must not be zero",
                    }
                ],
            },
        )

    direction = MetricDirection(payload.fallback_direction)
    directions = (
        {name: MetricDirection(value) for name, value in payload.directions.items()}
        if payload.directions
        else None
    )
    results = compare_benchmark_metrics(
        baseline_metrics=payload.baseline,
        current_metrics=payload.current,
        threshold_percent=payload.threshold_percent,
        direction=direction,
        directions=directions,
    )
    summary = build_pr_gate_summary(results)
    triage = generate_triage_notes(results)
    workflow_context = select_dashboard_workflow_context(
        use_sample_data=payload.use_sample_data,
        has_directions_upload=payload.directions is not None,
    )
    workflow = generate_github_actions_workflow(
        baseline_path=workflow_context.baseline_path,
        current_path=workflow_context.current_path,
        directions_config_path=workflow_context.directions_config_path,
        threshold=payload.threshold_percent,
        direction=direction,
    )

    return {
        "compared_metric_count": summary.compared_metrics,
        "regression_count": summary.regression_count,
        "release_readiness_score": summary.readiness_score,
        "release_readiness_label": summary.readiness_label,
        "recommendation": summary.recommendation,
        "should_block": summary.should_block,
        "metrics": [
            {
                "metric_name": result.metric_name,
                "baseline": result.baseline_value,
                "current": result.current_value,
                "percentage_change": result.change_percent,
                "threshold": result.threshold_percent,
                "direction": result.direction.value,
                "is_regression": result.is_regression,
                "severity": result.severity,
            }
            for result in results
        ],
        "triage_notes": [
            {
                "metric_name": note.metric_name,
                "likely_area": note.likely_area,
                "why_it_matters": note.why_it_matters,
                "suggested_checks": list(note.suggested_checks),
            }
            for note in triage
        ],
        "markdown_report": generate_markdown_report(results),
        "html_report": generate_html_report(results),
        "codex_fix_prompt": generate_codex_fix_prompt(results),
        "github_issue": generate_github_issue(results),
        "ci_workflow": workflow,
        "release_readiness_markdown": generate_release_readiness_markdown(results),
    }
