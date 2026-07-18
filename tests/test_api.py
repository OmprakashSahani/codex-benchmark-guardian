import asyncio
import json
import math

import httpx
import pytest

from api.index import MAX_METRICS, app


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
