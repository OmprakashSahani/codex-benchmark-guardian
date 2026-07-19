import asyncio
import json
import math

import httpx
import pytest

from api.index import MAX_METRICS, app
from codex_benchmark_guardian.benchmarks import compare_benchmark_metrics
from codex_benchmark_guardian.regression import MetricDirection
from codex_benchmark_guardian.repair import (
    build_repair_contract,
    generate_codex_repair_goal,
    generate_repair_contract_json,
    generate_repair_contract_markdown,
)


def request(method: str, url: str, **kwargs) -> httpx.Response:
    async def send() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.request(method, url, **kwargs)

    return asyncio.run(send())


def sample_payload() -> dict:
    return {
        "baseline": {
            "latency_ms": 100.0,
            "memory_mb": 256.0,
            "runtime_s": 2.5,
            "throughput_rps": 1000.0,
        },
        "current": {
            "latency_ms": 125.0,
            "memory_mb": 260.0,
            "runtime_s": 2.7,
            "throughput_rps": 850.0,
        },
        "threshold_percent": 10.0,
        "fallback_direction": "higher_is_worse",
        "directions": {"throughput_rps": "lower_is_worse"},
    }


def no_regression_payload() -> dict:
    payload = sample_payload()
    payload["current"] = payload["baseline"].copy()
    return payload


def canonical_repair_outputs(payload: dict) -> tuple[dict, str, str, str]:
    fallback_direction = MetricDirection(payload["fallback_direction"])
    directions = (
        {
            name: MetricDirection(direction)
            for name, direction in payload.get("directions", {}).items()
        }
        if payload.get("directions")
        else None
    )
    results = compare_benchmark_metrics(
        baseline_metrics=payload["baseline"],
        current_metrics=payload["current"],
        threshold_percent=payload["threshold_percent"],
        direction=fallback_direction,
        directions=directions,
    )
    contract = build_repair_contract(results)
    contract_json = generate_repair_contract_json(contract)
    return (
        json.loads(contract_json),
        generate_repair_contract_markdown(contract),
        contract_json,
        generate_codex_repair_goal(contract),
    )


def test_health_endpoint() -> None:
    assert request("GET", "/api/health").json() == {"status": "ok"}


def test_invalid_json_has_safe_validation_error() -> None:
    response = request(
        "POST",
        "/api/analyze",
        content="{",
        headers={"content-type": "application/json"},
    )
    assert response.status_code == 422
    assert response.json()["error"] == "Invalid analysis request"
    assert "traceback" not in response.text.lower()


def test_successful_sample_analysis() -> None:
    response = request("POST", "/api/analyze", json=sample_payload())
    assert response.status_code == 200
    assert response.json()["compared_metric_count"] == 4
    assert response.json()["regression_count"] == 2


def test_mixed_metric_directions() -> None:
    response = request("POST", "/api/analyze", json=sample_payload())
    metrics = {item["metric_name"]: item for item in response.json()["metrics"]}
    assert metrics["latency_ms"]["is_regression"] is True
    assert metrics["throughput_rps"]["direction"] == "lower_is_worse"
    assert metrics["throughput_rps"]["is_regression"] is True


def test_sample_analysis_workflow_uses_existing_example_paths() -> None:
    payload = sample_payload()
    payload["use_sample_data"] = True
    workflow = request("POST", "/api/analyze", json=payload).json()["ci_workflow"]

    assert "'examples/baseline.json'" in workflow
    assert "'examples/current.json'" in workflow
    assert "'examples/directions.json'" in workflow
    assert "benchmarks/baseline.json" not in workflow
    assert "benchmarks/current.json" not in workflow


def test_custom_analysis_workflow_uses_custom_paths() -> None:
    payload = sample_payload()
    payload["use_sample_data"] = False
    workflow = request("POST", "/api/analyze", json=payload).json()["ci_workflow"]

    assert "'benchmarks/baseline.json'" in workflow
    assert "'benchmarks/current.json'" in workflow
    assert "'benchmarks/directions.json'" in workflow


def test_custom_analysis_without_directions_omits_directions_config() -> None:
    payload = sample_payload()
    payload.pop("directions")
    payload["use_sample_data"] = False
    workflow = request("POST", "/api/analyze", json=payload).json()["ci_workflow"]

    assert "'benchmarks/baseline.json'" in workflow
    assert "'benchmarks/current.json'" in workflow
    assert "--directions-config" not in workflow
    assert "benchmarks/directions.json" not in workflow


def test_custom_analysis_with_null_directions_omits_directions_config() -> None:
    payload = sample_payload()
    payload["directions"] = None
    workflow = request("POST", "/api/analyze", json=payload).json()["ci_workflow"]

    assert "--directions-config" not in workflow
    assert "benchmarks/directions.json" not in workflow


def test_custom_analysis_with_empty_directions_preserves_config_path() -> None:
    payload = sample_payload()
    payload["directions"] = {}
    data = request("POST", "/api/analyze", json=payload).json()
    throughput = next(
        metric for metric in data["metrics"] if metric["metric_name"] == "throughput_rps"
    )

    assert "'benchmarks/directions.json'" in data["ci_workflow"]
    assert throughput["direction"] == "higher_is_worse"
    assert throughput["is_regression"] is False


def test_omitted_sample_flag_defaults_to_custom_workflow() -> None:
    payload = sample_payload()
    assert "use_sample_data" not in payload
    response = request("POST", "/api/analyze", json=payload)

    assert response.status_code == 200
    assert "'benchmarks/baseline.json'" in response.json()["ci_workflow"]


@pytest.mark.parametrize("threshold", [-1, "ten", math.inf])
def test_invalid_threshold(threshold) -> None:
    payload = sample_payload()
    payload["threshold_percent"] = threshold
    kwargs = (
        {"content": json.dumps(payload), "headers": {"content-type": "application/json"}}
        if isinstance(threshold, float) and not math.isfinite(threshold)
        else {"json": payload}
    )
    assert request("POST", "/api/analyze", **kwargs).status_code == 422


def test_invalid_direction() -> None:
    payload = sample_payload()
    payload["directions"] = {"latency_ms": "sideways"}
    assert request("POST", "/api/analyze", json=payload).status_code == 422


def test_nonnumeric_input() -> None:
    payload = sample_payload()
    payload["baseline"]["latency_ms"] = "fast"
    assert request("POST", "/api/analyze", json=payload).status_code == 422


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_non_finite_values(value: float) -> None:
    payload = sample_payload()
    payload["current"]["latency_ms"] = value
    response = request(
        "POST",
        "/api/analyze",
        content=json.dumps(payload),
        headers={"content-type": "application/json"},
    )
    assert response.status_code == 422


def test_no_matching_metrics() -> None:
    payload = sample_payload()
    payload["baseline"] = {"latency_ms": 100}
    payload["current"] = {"throughput_rps": 90}
    assert request("POST", "/api/analyze", json=payload).status_code == 422


def test_maximum_metric_count_protection() -> None:
    payload = sample_payload()
    payload["baseline"] = {f"metric_{index}": index + 1 for index in range(MAX_METRICS + 1)}
    assert request("POST", "/api/analyze", json=payload).status_code == 422


def test_response_readiness_and_artifact_fields() -> None:
    data = request("POST", "/api/analyze", json=sample_payload()).json()
    assert (data["release_readiness_score"], data["release_readiness_label"]) == (50, "Block")
    assert data["should_block"] is True
    for field in (
        "markdown_report",
        "html_report",
        "codex_fix_prompt",
        "github_issue",
        "ci_workflow",
        "release_readiness_markdown",
    ):
        assert data[field]
    assert len(data["triage_notes"]) == 2


def test_regression_response_exposes_canonical_repair_contract() -> None:
    payload = sample_payload()
    data = request("POST", "/api/analyze", json=payload).json()
    expected_contract, expected_markdown, expected_json, expected_goal = canonical_repair_outputs(
        payload
    )

    assert data["repair_contract"] == expected_contract
    assert data["repair_contract_markdown"] == expected_markdown
    assert data["repair_contract_json"] == expected_json
    assert data["codex_repair_goal"] == expected_goal
    assert data["repair_contract"]["repair_required"] is True
    assert data["repair_contract"]["regressed_metrics"] == [
        {
            "metric_name": metric["metric_name"],
            "baseline": metric["baseline"],
            "current": metric["current"],
            "percentage_change": metric["percentage_change"],
            "threshold": metric["threshold"],
            "direction": metric["direction"],
            "severity": metric["severity"],
        }
        for metric in data["metrics"]
        if metric["is_regression"]
    ]
    completion = " ".join(data["repair_contract"]["completion_criteria"])
    assert "protected workflow or trusted evaluator" in completion
    assert "zero material regressions" in completion
    assert "readiness as Ready" in completion
    assert "final diff is reviewed" in completion
    assert "Human approval remains required before merge" in completion
    assert all(
        data[field]
        for field in (
            "repair_contract_markdown",
            "repair_contract_json",
            "codex_repair_goal",
        )
    )


def test_no_regression_response_exposes_verification_only_contract() -> None:
    payload = no_regression_payload()
    data = request("POST", "/api/analyze", json=payload).json()
    expected_contract, expected_markdown, expected_json, expected_goal = canonical_repair_outputs(
        payload
    )

    assert data["repair_contract"] == expected_contract
    assert data["repair_contract_markdown"] == expected_markdown
    assert data["repair_contract_json"] == expected_json
    assert data["codex_repair_goal"] == expected_goal
    contract = data["repair_contract"]
    assert contract["repair_required"] is False
    assert "No repair is required" in contract["repair_objective"]
    allowed = " ".join(contract["allowed_actions"]).lower()
    assert "protected workflow or trusted evaluator" in allowed
    assert "implement" not in allowed
    assert "add or update regression tests" not in allowed
    assert "speculative code or test changes" in data["codex_repair_goal"]
    assert "Inspect, repair, review, validate, and repeat" not in data["codex_repair_goal"]
    completion = " ".join(contract["completion_criteria"])
    assert "zero material regressions" in completion
    assert "readiness as Ready" in completion
    assert "Human approval remains required before merge" in completion


@pytest.mark.parametrize("payload", [sample_payload(), no_regression_payload()])
def test_repair_response_is_deterministic_and_internally_consistent(payload: dict) -> None:
    first = request("POST", "/api/analyze", json=payload).json()
    second = request("POST", "/api/analyze", json=payload).json()

    assert first["repair_contract"] == second["repair_contract"]
    for field in (
        "repair_contract_markdown",
        "repair_contract_json",
        "codex_repair_goal",
    ):
        assert first[field] == second[field]
    assert json.loads(first["repair_contract_json"]) == first["repair_contract"]


def test_repair_fields_are_additive_and_preserve_existing_response() -> None:
    data = request("POST", "/api/analyze", json=sample_payload()).json()
    existing_fields = {
        "compared_metric_count",
        "regression_count",
        "release_readiness_score",
        "release_readiness_label",
        "recommendation",
        "should_block",
        "metrics",
        "triage_notes",
        "markdown_report",
        "html_report",
        "codex_fix_prompt",
        "github_issue",
        "ci_workflow",
        "release_readiness_markdown",
    }

    assert existing_fields <= data.keys()
    assert data["compared_metric_count"] == 4
    assert data["regression_count"] == 2
    assert data["release_readiness_score"] == 50
    assert data["release_readiness_label"] == "Block"
    assert data["should_block"] is True
    assert isinstance(data["metrics"], list)
    assert isinstance(data["triage_notes"], list)
    assert isinstance(data["codex_fix_prompt"], str)
    assert data["codex_fix_prompt"]


def test_untrusted_metric_name_uses_canonical_safe_repair_rendering() -> None:
    metric_name = "latency|extra\n## Injected\n![image](https://example.com/x)\n<img src=x>"
    payload = {
        "baseline": {metric_name: 100.0},
        "current": {metric_name: 125.0},
        "threshold_percent": 10.0,
        "fallback_direction": "higher_is_worse",
    }
    data = request("POST", "/api/analyze", json=payload).json()
    expected_contract, expected_markdown, expected_json, expected_goal = canonical_repair_outputs(
        payload
    )

    assert data["repair_contract"] == expected_contract
    assert data["repair_contract_markdown"] == expected_markdown
    assert data["repair_contract_json"] == expected_json
    assert data["codex_repair_goal"] == expected_goal
    assert data["repair_contract"]["regressed_metrics"][0]["metric_name"] == metric_name
    assert (
        json.loads(data["repair_contract_json"])["regressed_metrics"][0]["metric_name"]
        == metric_name
    )
    for artifact in (data["repair_contract_markdown"], data["codex_repair_goal"]):
        assert "latency&#124;extra" in artifact
        assert "\n## Injected" not in artifact
        assert "![image]" not in artifact
        assert "<img" not in artifact
        evidence_lines = [line for line in artifact.splitlines() if "latency&#124;extra" in line]
        assert len(evidence_lines) == 1
        assert evidence_lines[0].count(" | ") == 6


def test_empty_evidence_keeps_existing_validation_response() -> None:
    payload = sample_payload()
    payload["baseline"] = {}
    response = request("POST", "/api/analyze", json=payload)

    assert response.status_code == 422
    assert response.json()["error"] == "Invalid analysis request"
    assert response.json()["details"] == [
        {"field": "baseline", "message": "Value error, must contain at least one metric"}
    ]
