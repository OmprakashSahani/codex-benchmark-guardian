"use client";

import { Activity, BarChart3, Bot, ClipboardList, FileCode2, LayoutDashboard } from "lucide-react";
import { useEffect, useId, useRef, useState } from "react";
import type { AnalysisResponse } from "@/lib/types";
import { Card } from "./ui";
import { DecisionSummary } from "./decision-summary";
import { HandoffPack } from "./handoff-pack";
import { MetricChangeChart } from "./metric-change-chart";
import { MetricsTable } from "./metrics-table";
import { TriagePanel } from "./triage-panel";
import { CodexFixPanel } from "./codex-fix-panel";

const tabs = [
  { id: "overview", label: "Overview", icon: LayoutDashboard },
  { id: "metrics", label: "Metrics", icon: BarChart3 },
  { id: "triage", label: "Triage", icon: ClipboardList },
  { id: "codex-fix", label: "Codex Goal", icon: Bot },
  { id: "handoff", label: "Handoff Pack", icon: FileCode2 },
] as const;
type TabId = (typeof tabs)[number]["id"];

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
  const [selected, setSelected] = useState<TabId>("overview");
  const [announcement, setAnnouncement] = useState("");
  const tabRefs = useRef<Array<HTMLButtonElement | null>>([]);
  const instanceId = useId();
  const tabId = (id: TabId) => `${instanceId}-tab-${id}`;
  const panelId = (id: TabId) => `${instanceId}-panel-${id}`;

  useEffect(() => {
    setAnnouncement(`New benchmark result: ${result.release_readiness_label}, readiness score ${result.release_readiness_score} out of 100, with ${result.regression_count} regressions.`);
  }, [result.regression_count, result.release_readiness_label, result.release_readiness_score]);

  function selectByIndex(index: number) {
    const next = (index + tabs.length) % tabs.length;
    setSelected(tabs[next].id);
    tabRefs.current[next]?.focus();
  }

  return (
    <section className="results" aria-label="Benchmark analysis result">
      <p className="sr-only" role="status" aria-live="polite">{announcement}</p>
      <DecisionSummary result={result} />
      <Card className="result-details">
        <div className="tabs" role="tablist" aria-label="Analysis result sections">
          {tabs.map((tab, index) => <button key={tab.id} ref={(node) => { tabRefs.current[index] = node; }} id={tabId(tab.id)} type="button" role="tab" aria-selected={selected === tab.id} aria-controls={panelId(tab.id)} tabIndex={selected === tab.id ? 0 : -1} onClick={() => setSelected(tab.id)} onKeyDown={(event) => {
            if (event.key === "ArrowRight") { event.preventDefault(); selectByIndex(index + 1); }
            if (event.key === "ArrowLeft") { event.preventDefault(); selectByIndex(index - 1); }
            if (event.key === "Home") { event.preventDefault(); selectByIndex(0); }
            if (event.key === "End") { event.preventDefault(); selectByIndex(tabs.length - 1); }
          }}><tab.icon size={16} /><span>{tab.label}</span>{tab.id === "triage" && result.regression_count > 0 && <b>{result.regression_count}</b>}</button>)}
        </div>
        <div className="tab-panel" id={panelId("overview")} role="tabpanel" aria-labelledby={tabId("overview")} tabIndex={0} hidden={selected !== "overview"}><MetricChangeChart metrics={result.metrics} /></div>
        <div className="tab-panel" id={panelId("metrics")} role="tabpanel" aria-labelledby={tabId("metrics")} tabIndex={0} hidden={selected !== "metrics"}><MetricsTable metrics={result.metrics} /></div>
        <div className="tab-panel" id={panelId("triage")} role="tabpanel" aria-labelledby={tabId("triage")} tabIndex={0} hidden={selected !== "triage"}><TriagePanel notes={result.triage_notes} /></div>
        <div className="tab-panel" id={panelId("codex-fix")} role="tabpanel" aria-labelledby={tabId("codex-fix")} tabIndex={0} hidden={selected !== "codex-fix"}><CodexFixPanel result={result} /></div>
        <div className="tab-panel" id={panelId("handoff")} role="tabpanel" aria-labelledby={tabId("handoff")} tabIndex={0} hidden={selected !== "handoff"}><HandoffPack result={result} /></div>
      </Card>
    </section>
  );
}
