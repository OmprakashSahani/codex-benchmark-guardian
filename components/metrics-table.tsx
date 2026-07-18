import { AlertTriangle, CheckCircle2 } from "lucide-react";
import { formatNumber, formatNumberPair, formatPercentage } from "@/lib/number-format";
import type { MetricResult } from "@/lib/types";
import { Badge } from "./ui";

export function MetricsTable({ metrics }: { metrics: MetricResult[] }) {
  return <section aria-labelledby="metrics-title"><div className="detail-heading"><div><span className="eyebrow">Metric detail</span><h3 id="metrics-title">Full comparison results</h3><p>Source values and evaluator classifications are preserved below.</p></div><Badge>{metrics.length} metrics</Badge></div>
    <div className="table-scroll"><table><caption>Baseline and current benchmark values, percentage change, direction, threshold, and evaluator status for every metric.</caption><thead><tr><th scope="col">Metric</th><th scope="col">Baseline</th><th scope="col">Current</th><th scope="col">Change</th><th scope="col">Direction</th><th scope="col">Threshold</th><th scope="col">Status / severity</th></tr></thead>
      <tbody>{metrics.map((metric) => {
        const [baseline, current] = formatNumberPair(metric.baseline, metric.current);
        return <tr key={metric.metric_name} className={metric.is_regression ? "regression-row" : undefined}>
          <th scope="row" className="metric-name" title={metric.metric_name}>{metric.metric_name}</th><td>{baseline}</td><td>{current}</td><td className={metric.is_regression ? "danger" : ""}>{formatPercentage(metric.percentage_change)}</td><td><code>{metric.direction}</code></td><td>{formatNumber(metric.threshold)}%</td><td><Badge tone={metric.is_regression ? "block" : "ready"}>{metric.is_regression ? <><AlertTriangle size={12} />Regression · {metric.severity}</> : <><CheckCircle2 size={12} />No regression</>}</Badge></td>
        </tr>;
      })}</tbody></table></div>
  </section>;
}
