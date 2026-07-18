import { AlertTriangle, CheckCircle2, ShieldAlert } from "lucide-react";
import type { AnalysisResponse } from "@/lib/types";
import { Badge, Card } from "./ui";

function tone(label: AnalysisResponse["release_readiness_label"]) {
  return label === "Ready" ? "ready" : label === "Needs Review" ? "review" : "block";
}

export function DecisionSummary({ result }: { result: AnalysisResponse }) {
  const statusTone = tone(result.release_readiness_label);
  const StatusIcon = result.should_block ? ShieldAlert : result.regression_count ? AlertTriangle : CheckCircle2;
  const score = Math.max(0, Math.min(100, result.release_readiness_score));
  return <Card className={`decision-summary decision-${statusTone}`}>
    <div className="decision-main">
      <div className="decision-label"><Badge tone={statusTone}><StatusIcon size={13} />{result.release_readiness_label}</Badge><span>Release decision</span></div>
      <h2>{result.recommendation}</h2>
      <p>Deterministic assessment from the Python benchmark engine.</p>
      <dl className="decision-facts">
        <div><dt>Compared metrics</dt><dd>{result.compared_metric_count}</dd></div>
        <div><dt>Regressions</dt><dd>{result.regression_count}</dd></div>
        <div><dt>Gate status</dt><dd>{result.should_block ? "Blocked" : "Clear"}</dd></div>
      </dl>
    </div>
    <div className="score-ring" role="img" aria-label={`Release-readiness score: ${result.release_readiness_score} out of 100`} style={{ "--score": score } as React.CSSProperties}>
      <svg viewBox="0 0 120 120" aria-hidden="true"><circle className="score-track" cx="60" cy="60" r="51" /><circle className="score-value" cx="60" cy="60" r="51" pathLength="100" /></svg>
      <span><strong>{result.release_readiness_score}</strong><small>/ 100</small><em>Readiness</em></span>
    </div>
  </Card>;
}
