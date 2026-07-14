from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from codex_benchmark_guardian.regression import RegressionResult


@dataclass(frozen=True)
class TriageNote:
    """Developer-facing guidance for a regressed benchmark metric."""

    metric_name: str
    likely_area: str
    why_it_matters: str
    suggested_checks: tuple[str, ...]


def generate_triage_notes(results: Sequence[RegressionResult]) -> list[TriageNote]:
    """Generate triage notes for regressed metrics only."""
    return [triage_regression(result) for result in results if result.is_regression]


def triage_regression(result: RegressionResult) -> TriageNote:
    """Generate deterministic triage guidance for one regressed metric."""
    metric_name = result.metric_name
    normalized_name = metric_name.lower()

    if "latency" in normalized_name or normalized_name == "latency_ms":
        return TriageNote(
            metric_name=metric_name,
            likely_area="Request path latency or dependency wait time",
            why_it_matters=(
                "Higher latency slows developer and user workflows and can hide downstream "
                "bottlenecks."
            ),
            suggested_checks=(
                (
                    "Inspect recent changes on the hot path for added I/O, sleeps, "
                    "retries, or serialization work."
                ),
                (
                    "Compare dependency timing, network calls, database queries, "
                    "and cache hit rates against the baseline."
                ),
                "Check benchmark host load and input size to rule out environmental noise.",
            ),
        )

    if "runtime" in normalized_name or normalized_name == "runtime_s":
        return TriageNote(
            metric_name=metric_name,
            likely_area="Overall execution time or algorithmic complexity",
            why_it_matters=(
                "Longer runtime increases feedback-loop duration and may indicate "
                "less efficient code paths."
            ),
            suggested_checks=(
                "Profile the benchmark to find functions with the largest wall-clock increase.",
                "Review loops, sorting, parsing, and data structure changes for worse complexity.",
                (
                    "Confirm setup and teardown work was not accidentally included "
                    "in the measured path."
                ),
            ),
        )

    if "memory" in normalized_name or normalized_name == "memory_mb":
        return TriageNote(
            metric_name=metric_name,
            likely_area="Memory allocation, object retention, or working-set growth",
            why_it_matters=(
                "Higher memory use can increase costs, trigger garbage collection, "
                "and reduce reliability under load."
            ),
            suggested_checks=(
                (
                    "Compare allocation profiles for new large collections, buffers, "
                    "or duplicated payloads."
                ),
                (
                    "Look for caches, globals, or retained references that now "
                    "outlive the benchmark iteration."
                ),
                "Check whether batch sizes, fixture sizes, or response payloads changed.",
            ),
        )

    if "throughput" in normalized_name or normalized_name == "throughput_rps":
        return TriageNote(
            metric_name=metric_name,
            likely_area="Capacity, concurrency, or request processing rate",
            why_it_matters=(
                "Lower throughput means the system handles less work with the same resources."
            ),
            suggested_checks=(
                (
                    "Review concurrency limits, worker counts, queue behavior, "
                    "and backpressure changes."
                ),
                (
                    "Inspect CPU, lock contention, database pool usage, and "
                    "external service rate limits."
                ),
                "Verify the benchmark duration and request mix match the baseline run.",
            ),
        )

    if any(
        pattern in normalized_name
        for pattern in ("accuracy", "recall", "precision", "success_rate")
    ):
        return TriageNote(
            metric_name=metric_name,
            likely_area="Correctness, model quality, or successful completion rate",
            why_it_matters=(
                "Lower quality metrics can mean users receive less accurate or "
                "less reliable results."
            ),
            suggested_checks=(
                (
                    "Compare failing cases against the baseline to identify common "
                    "inputs or categories."
                ),
                "Review prompt, scoring, filtering, threshold, and data preprocessing changes.",
                "Confirm evaluation data, random seeds, and success criteria stayed consistent.",
            ),
        )

    return TriageNote(
        metric_name=metric_name,
        likely_area="Metric-specific benchmark behavior",
        why_it_matters=(
            "A regression indicates the metric moved beyond the configured "
            "threshold and needs owner review."
        ),
        suggested_checks=(
            "Confirm the metric direction and threshold match the intended benchmark semantics.",
            (
                "Review recent code, dependency, configuration, and fixture changes "
                "that affect this metric."
            ),
            "Rerun the benchmark to confirm the signal is stable before deciding on remediation.",
        ),
    )
