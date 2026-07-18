import { scenariosById } from "./example-scenarios";
import type { Direction } from "./types";

export interface PrReplayFixture {
  readonly kind: "regression" | "verified-fix";
  readonly scenarioId: "pr-20-regression" | "pr-20-verified-fix";
  readonly baseline: Readonly<Record<string, number>>;
  readonly current: Readonly<Record<string, number>>;
  readonly directions: Readonly<Record<string, Direction>>;
  readonly threshold: number;
  readonly fallbackDirection: Direction;
  readonly workflowUrl: string;
}

function replayFixture(scenarioId: PrReplayFixture["scenarioId"], kind: PrReplayFixture["kind"]): PrReplayFixture {
  const scenario = scenariosById[scenarioId];
  if (!scenario.workflowUrl) throw new Error(`Missing workflow URL for ${scenarioId}`);
  return {
    kind,
    scenarioId,
    baseline: scenario.baseline,
    current: scenario.current,
    directions: scenario.directions,
    threshold: scenario.thresholdPercent,
    fallbackDirection: scenario.fallbackDirection,
    workflowUrl: scenario.workflowUrl,
  };
}

export const PR_DEMO_DIRECTIONS = scenariosById["pr-20-regression"].directions;
export const PR_REGRESSION_REPLAY = replayFixture("pr-20-regression", "regression");
export const PR_VERIFIED_FIX_REPLAY = replayFixture("pr-20-verified-fix", "verified-fix");
export const PR_20_URL = scenariosById["pr-20-regression"].pullRequestUrl!;
