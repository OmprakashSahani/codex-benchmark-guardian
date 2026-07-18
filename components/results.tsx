import { Activity, AlertTriangle, CheckCircle2, Gauge, ShieldAlert } from "lucide-react";
import type { AnalysisResponse } from "@/lib/types";
import { Badge, Card } from "./ui";

function tone(label: AnalysisResponse["release_readiness_label"]) {
  return label === "Ready" ? "ready" : label === "Needs Review" ? "review" : "block";
}

export function EmptyResults() {
  return (
    <Card className="empty-state">
      <span className="empty-icon"><Activity size={26} /></span>
      <h2>Your benchmark decision will appear here</h2>
      <p>Provide baseline and current metrics, set the regression policy, then run the deterministic analysis.</p>
      <div className="empty-steps"><span>1. Add JSON</span><span>2. Configure threshold</span><span>3. Review readiness</span></div>
    </Card>
  );
}

export function Results({ result }: { result: AnalysisResponse }) {
  const statusTone = tone(result.release_readiness_label);
  const StatusIcon = result.should_block ? ShieldAlert : result.regression_count ? AlertTriangle : CheckCircle2;
  return (
    <section className="results" aria-live="polite">
      <Card className={`decision decision-${statusTone}`}>
        <div className="decision-copy">
          <Badge tone={statusTone}>{result.release_readiness_label}</Badge>
          <h2><StatusIcon size={28} /> Release decision</h2>
          <p>{result.recommendation}</p>
        </div>
        <div className="score" aria-label={`${result.release_readiness_score} out of 100`}>
          <Gauge size={20} /><strong>{result.release_readiness_score}</strong><span>/ 100</span>
        </div>
      </Card>
      <div className="metric-cards">
        <Card><span>Compared metrics</span><strong>{result.compared_metric_count}</strong></Card>
        <Card><span>Regressions</span><strong className={result.regression_count ? "danger" : "success"}>{result.regression_count}</strong></Card>
        <Card><span>Gate status</span><strong>{result.should_block ? "Blocked" : "Clear"}</strong></Card>
      </div>
      <Card className="table-card">
        <div className="section-heading"><div><span className="eyebrow">Metric detail</span><h2>Comparison results</h2></div><Badge>{result.metrics.length} metrics</Badge></div>
        <div className="table-scroll"><table><thead><tr><th>Metric</th><th>Baseline</th><th>Current</th><th>Change</th><th>Direction</th><th>Status</th></tr></thead>
          <tbody>{result.metrics.map((metric) => <tr key={metric.metric_name}>
            <td className="metric-name">{metric.metric_name}</td><td>{metric.baseline}</td><td>{metric.current}</td>
            <td className={metric.is_regression ? "danger" : ""}>{metric.percentage_change > 0 ? "+" : ""}{metric.percentage_change.toFixed(2)}%</td>
            <td><code>{metric.direction}</code></td><td><Badge tone={metric.is_regression ? "block" : "ready"}>{metric.is_regression ? metric.severity : "OK"}</Badge></td>
          </tr>)}</tbody>
        </table></div>
      </Card>
    </section>
  );
}
