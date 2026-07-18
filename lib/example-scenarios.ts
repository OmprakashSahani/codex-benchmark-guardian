import catalogue from "@/examples/scenarios/scenarios.json";
import standardBaseline from "@/examples/scenarios/standard/baseline.json";
import standardCurrent from "@/examples/scenarios/standard/current.json";
import standardDirections from "@/examples/scenarios/standard/directions.json";
import cleanBaseline from "@/examples/scenarios/clean/baseline.json";
import cleanCurrent from "@/examples/scenarios/clean/current.json";
import cleanDirections from "@/examples/scenarios/clean/directions.json";
import prRegressionBaseline from "@/examples/scenarios/pr-20/regression/baseline.json";
import prRegressionCurrent from "@/examples/scenarios/pr-20/regression/current.json";
import prRegressionDirections from "@/examples/scenarios/pr-20/regression/directions.json";
import prFixBaseline from "@/examples/scenarios/pr-20/verified-fix/baseline.json";
import prFixCurrent from "@/examples/scenarios/pr-20/verified-fix/current.json";
import prFixDirections from "@/examples/scenarios/pr-20/verified-fix/directions.json";
import type { Direction } from "./types";

export type ScenarioId = "standard" | "material" | "clean" | "pr-20-regression" | "pr-20-verified-fix";
export type ScenarioSelection = ScenarioId | "custom";

export interface ExampleScenario {
  readonly id: ScenarioId;
  readonly label: string;
  readonly description: string;
  readonly baselinePath: string;
  readonly currentPath: string;
  readonly directionsPath: string;
  readonly thresholdPercent: number;
  readonly fallbackDirection: Direction;
  readonly useSampleData: boolean;
  readonly expectedComparedMetricCount: number;
  readonly expectedRegressionCount: number;
  readonly expectedReadinessScore: number;
  readonly expectedReadinessLabel: "Ready" | "Needs Review" | "Block";
  readonly sourceType: string;
  readonly pullRequestUrl?: string;
  readonly workflowUrl?: string;
  readonly baseline: Readonly<Record<string, number>>;
  readonly current: Readonly<Record<string, number>>;
  readonly directions: Readonly<Record<string, Direction>>;
}

const evidence = {
  standard: { baseline: standardBaseline, current: standardCurrent, directions: standardDirections as Record<string, Direction> },
  material: { baseline: standardBaseline, current: standardCurrent, directions: standardDirections as Record<string, Direction> },
  clean: { baseline: cleanBaseline, current: cleanCurrent, directions: cleanDirections as Record<string, Direction> },
  "pr-20-regression": { baseline: prRegressionBaseline, current: prRegressionCurrent, directions: prRegressionDirections as Record<string, Direction> },
  "pr-20-verified-fix": { baseline: prFixBaseline, current: prFixCurrent, directions: prFixDirections as Record<string, Direction> },
} satisfies Record<ScenarioId, { baseline: Record<string, number>; current: Record<string, number>; directions: Record<string, Direction> }>;

export const exampleScenarios: readonly ExampleScenario[] = catalogue.map((item) => {
  const id = item.id as ScenarioId;
  return {
    id,
    label: item.label,
    description: item.description,
    baselinePath: item.baseline_path,
    currentPath: item.current_path,
    directionsPath: item.directions_path,
    thresholdPercent: item.threshold_percent,
    fallbackDirection: item.fallback_direction as Direction,
    useSampleData: item.use_sample_data,
    expectedComparedMetricCount: item.expected_compared_metric_count,
    expectedRegressionCount: item.expected_regression_count,
    expectedReadinessScore: item.expected_readiness_score,
    expectedReadinessLabel: item.expected_readiness_label as ExampleScenario["expectedReadinessLabel"],
    sourceType: item.source_type,
    pullRequestUrl: "pull_request_url" in item ? item.pull_request_url : undefined,
    workflowUrl: "workflow_url" in item ? item.workflow_url : undefined,
    ...evidence[id],
  };
});

export const scenariosById = Object.fromEntries(exampleScenarios.map((scenario) => [scenario.id, scenario])) as Record<ScenarioId, ExampleScenario>;
export const DEFAULT_SCENARIO = scenariosById.standard;
export const SCENARIOS_GITHUB_URL = "https://github.com/OmprakashSahani/codex-benchmark-guardian/tree/main/examples/scenarios";
