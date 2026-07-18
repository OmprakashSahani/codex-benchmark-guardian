import { AlertTriangle } from "lucide-react";
import type { MetricResult } from "@/lib/types";
import { formatPercentage } from "@/lib/number-format";

export function MetricChangeChart({ metrics }: { metrics: MetricResult[] }) {
  const max = metrics.reduce((largest, metric) => {
    const absolute = Math.abs(metric.percentage_change);
    return Number.isFinite(absolute) && absolute > largest ? absolute : largest;
  }, 0);
  return <section className="change-chart" aria-labelledby="change-chart-title">
    <div className="detail-heading"><div><span className="eyebrow">Change profile</span><h3 id="change-chart-title">Metric deltas at a glance</h3><p>Centered at zero and scaled symmetrically to the largest absolute change ({formatPercentage(max)}).</p></div><span className="chart-legend"><i /> Regression <i /> Other change</span></div>
    <div className="delta-list" role="img" aria-label={`Horizontal comparison of ${metrics.length} metric percentage changes. Each row includes its exact value and regression status.`}>
      {metrics.map((metric) => {
        const change = Number.isFinite(metric.percentage_change) ? metric.percentage_change : 0;
        const width = max === 0 ? 0 : Math.min(50, Math.abs(change) / max * 50);
        return <div className="delta-row" key={metric.metric_name}>
          <span className="delta-name" title={metric.metric_name}>{metric.metric_name}</span>
          <div className="delta-track" aria-hidden="true"><span className="zero-line" /><span className={`delta-bar ${change < 0 ? "negative" : "positive"} ${metric.is_regression ? "regression" : ""}`} style={{ width: `${width}%`, [change < 0 ? "right" : "left"]: "50%" }} /></div>
          <span className={`delta-value ${metric.is_regression ? "danger" : ""}`}>{metric.is_regression && <AlertTriangle size={13} aria-label="Regression" />}{formatPercentage(change)}</span>
        </div>;
      })}
    </div>
  </section>;
}
