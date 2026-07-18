import type { Direction } from "./types";

export const PR_DEMO_DIRECTIONS = Object.freeze({
  comparison_latency_ms: "higher_is_worse",
  comparison_throughput_metrics_per_second: "lower_is_worse",
  pr_gate_generation_latency_ms: "higher_is_worse",
  report_generation_latency_ms: "higher_is_worse",
} satisfies Record<string, Direction>);

export interface PrReplayFixture {
  readonly kind: "regression" | "verified-fix";
  readonly baseline: Readonly<Record<string, number>>;
  readonly current: Readonly<Record<string, number>>;
  readonly directions: Readonly<Record<string, Direction>>;
  readonly threshold: number;
  readonly fallbackDirection: Direction;
  readonly workflowUrl: string;
}

export const PR_REGRESSION_REPLAY = Object.freeze({
  kind: "regression",
  threshold: 25,
  fallbackDirection: "higher_is_worse",
  directions: PR_DEMO_DIRECTIONS,
  baseline: Object.freeze({
    comparison_latency_ms: 1.14567092,
    comparison_throughput_metrics_per_second: 436425.49642440083,
    pr_gate_generation_latency_ms: 1.1398080400000001,
    report_generation_latency_ms: 4.413423679999999,
  }),
  current: Object.freeze({
    comparison_latency_ms: 1.14531728,
    comparison_throughput_metrics_per_second: 436560.2516710479,
    pr_gate_generation_latency_ms: 2.6809987000000004,
    report_generation_latency_ms: 4.45235926,
  }),
  workflowUrl: "https://github.com/OmprakashSahani/codex-benchmark-guardian/actions/runs/29634627579",
} satisfies PrReplayFixture);

export const PR_VERIFIED_FIX_REPLAY = Object.freeze({
  kind: "verified-fix",
  threshold: 25,
  fallbackDirection: "higher_is_worse",
  directions: PR_DEMO_DIRECTIONS,
  baseline: Object.freeze({
    comparison_latency_ms: 1.17001838,
    comparison_throughput_metrics_per_second: 427343.71403635555,
    pr_gate_generation_latency_ms: 1.15838182,
    report_generation_latency_ms: 4.4684764800000005,
  }),
  current: Object.freeze({
    comparison_latency_ms: 1.1581004799999999,
    comparison_throughput_metrics_per_second: 431741.4668544132,
    pr_gate_generation_latency_ms: 1.15482916,
    report_generation_latency_ms: 4.46952872,
  }),
  workflowUrl: "https://github.com/OmprakashSahani/codex-benchmark-guardian/actions/runs/29635217444",
} satisfies PrReplayFixture);

export const PR_20_URL = "https://github.com/OmprakashSahani/codex-benchmark-guardian/pull/20";
