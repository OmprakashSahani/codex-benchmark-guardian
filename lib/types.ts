export type Direction = "higher_is_worse" | "lower_is_worse";

export interface AnalysisRequest {
  baseline: Record<string, number>;
  current: Record<string, number>;
  threshold_percent: number;
  fallback_direction: Direction;
  directions?: Record<string, Direction> | null;
  use_sample_data: boolean;
}

export interface MetricResult {
  metric_name: string;
  baseline: number;
  current: number;
  percentage_change: number;
  threshold: number;
  direction: Direction;
  is_regression: boolean;
  severity: string;
}

export interface TriageNote {
  metric_name: string;
  likely_area: string;
  why_it_matters: string;
  suggested_checks: string[];
}

export interface AnalysisResponse {
  compared_metric_count: number;
  regression_count: number;
  release_readiness_score: number;
  release_readiness_label: "Ready" | "Needs Review" | "Block";
  recommendation: string;
  should_block: boolean;
  metrics: MetricResult[];
  triage_notes: TriageNote[];
  markdown_report: string;
  html_report: string;
  codex_fix_prompt: string;
  github_issue: string;
  ci_workflow: string;
  release_readiness_markdown: string;
}
