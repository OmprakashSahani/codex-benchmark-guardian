"use client";

import { Download, ExternalLink, Play, RotateCcw } from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { DEFAULT_SCENARIO, exampleScenarios, SCENARIOS_GITHUB_URL, scenariosById, type ExampleScenario, type ScenarioSelection } from "@/lib/example-scenarios";
import type { AnalysisRequest, AnalysisResponse, Direction } from "@/lib/types";
import type { PrReplayFixture } from "@/lib/pr-demo";
import { JsonUpload } from "./json-upload";
import { EmptyResults, Results } from "./results";
import { Button, Card } from "./ui";
import { PrReplay } from "./pr-replay";

const pretty = (value: object) => JSON.stringify(value, null, 2);

function parseMetrics(value: string): Record<string, number> {
  const parsed: unknown = JSON.parse(value);
  if (!parsed || Array.isArray(parsed) || typeof parsed !== "object") throw new Error("Metrics must be a JSON object.");
  const entries = Object.entries(parsed);
  if (entries.some(([, metric]) => typeof metric !== "number" || !Number.isFinite(metric))) throw new Error("Metric values must be finite numbers.");
  return Object.fromEntries(entries);
}

function isDirection(value: unknown): value is Direction {
  return value === "higher_is_worse" || value === "lower_is_worse";
}

function parseDirections(value: string): Record<string, Direction> {
  const parsed: unknown = JSON.parse(value);
  if (!parsed || Array.isArray(parsed) || typeof parsed !== "object") throw new Error("Directions must be a JSON object.");
  const entries = Object.entries(parsed);
  if (entries.some(([, direction]) => !isDirection(direction))) throw new Error("Directions must be higher_is_worse or lower_is_worse.");
  return Object.fromEntries(entries);
}

export function AnalysisWorkspace() {
  const [sample, setSample] = useState(true);
  const [scenarioId, setScenarioId] = useState<ScenarioSelection>(DEFAULT_SCENARIO.id);
  const [baseline, setBaseline] = useState(pretty(DEFAULT_SCENARIO.baseline));
  const [current, setCurrent] = useState(pretty(DEFAULT_SCENARIO.current));
  const [directions, setDirections] = useState(pretty(DEFAULT_SCENARIO.directions));
  const [names, setNames] = useState<Record<string, string>>({});
  const [threshold, setThreshold] = useState(10);
  const [fallback, setFallback] = useState<Direction>("higher_is_worse");
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [replayStatus, setReplayStatus] = useState("");
  const activeRequest = useRef<AbortController | null>(null);
  const mounted = useRef(true);
  const resultsArea = useRef<HTMLDivElement>(null);

  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      const controller = activeRequest.current;
      activeRequest.current = null;
      controller?.abort();
    };
  }, []);

  const invalidateAnalysis = useCallback(() => {
    activeRequest.current?.abort();
    activeRequest.current = null;
    setLoading(false);
    setResult(null);
    setError("");
    setReplayStatus("");
  }, []);

  const valid = useMemo(() => {
    try { JSON.parse(baseline); JSON.parse(current); if (directions.trim()) JSON.parse(directions); return Number.isFinite(threshold) && threshold >= 0; }
    catch { return false; }
  }, [baseline, current, directions, threshold]);

  const selectedScenario = scenarioId === "custom" ? undefined : scenariosById[scenarioId];

  const downloadable = useMemo(() => ({
    baseline: isJsonObject(baseline),
    current: isJsonObject(current),
    directions: Boolean(directions.trim()) && isJsonObject(directions),
  }), [baseline, current, directions]);

  function loadScenario(scenario: ExampleScenario) {
    invalidateAnalysis();
    setScenarioId(scenario.id); setSample(scenario.useSampleData); setNames({});
    setBaseline(pretty(scenario.baseline)); setCurrent(pretty(scenario.current)); setDirections(pretty(scenario.directions));
    setThreshold(scenario.thresholdPercent); setFallback(scenario.fallbackDirection);
  }

  function markCustom() { setScenarioId("custom"); setSample(false); }

  function toggleSample(enabled: boolean) {
    if (enabled) loadScenario(DEFAULT_SCENARIO);
    else { invalidateAnalysis(); setScenarioId("custom"); setSample(false); setNames({}); setBaseline(""); setCurrent(""); setDirections(""); }
  }

  async function runAnalysis(requestPayload: AnalysisRequest, successMessage = "") {
    const controller = new AbortController();
    activeRequest.current?.abort();
    activeRequest.current = controller;
    setLoading(true); setError(""); setResult(null); setReplayStatus("");
    try {
      const response = await fetch("/api/analyze", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(requestPayload), signal: controller.signal });
      const data = await response.json();
      if (!response.ok) throw new Error(data.details?.map((item: { field: string; message: string }) => `${item.field}: ${item.message}`).join(" · ") || data.error || "Analysis failed.");
      if (mounted.current && activeRequest.current === controller) {
        setResult(data);
        setReplayStatus(successMessage);
        if (successMessage) requestAnimationFrame(() => resultsArea.current?.scrollIntoView({ behavior: "smooth", block: "start" }));
      }
    } catch (reason) {
      if (mounted.current && activeRequest.current === controller && !controller.signal.aborted) setError(reason instanceof Error ? reason.message : "Analysis failed.");
    }
    finally {
      if (mounted.current && activeRequest.current === controller) {
        activeRequest.current = null;
        setLoading(false);
      }
    }
  }

  async function analyze() {
    setReplayStatus("");
    try {
      await runAnalysis({ baseline: parseMetrics(baseline), current: parseMetrics(current), threshold_percent: threshold, fallback_direction: fallback, directions: directions.trim() ? parseDirections(directions) : undefined, use_sample_data: sample });
    } catch (reason) {
      if (mounted.current) setError(reason instanceof Error ? reason.message : "Analysis failed.");
    }
  }

  function replay(fixture: PrReplayFixture) {
    const nextBaseline = pretty(fixture.baseline);
    const nextCurrent = pretty(fixture.current);
    const nextDirections = pretty(fixture.directions);
    setBaseline(nextBaseline); setCurrent(nextCurrent); setDirections(nextDirections); setThreshold(fixture.threshold); setFallback(fixture.fallbackDirection); setNames({}); setSample(false); setScenarioId(fixture.scenarioId);
    const message = fixture.kind === "regression" ? "Regression snapshot analyzed live" : "Verified fix snapshot analyzed live";
    void runAnalysis({ baseline: parseMetrics(nextBaseline), current: parseMetrics(nextCurrent), threshold_percent: fixture.threshold, fallback_direction: fixture.fallbackDirection, directions: parseDirections(nextDirections), use_sample_data: false }, message);
  }

  return (
    <section className="workspace" id="analysis">
      <div className="section-heading workspace-heading"><div><span className="eyebrow">Analysis workspace</span><h2>Compare benchmark evidence</h2><p>Inputs stay in memory and are evaluated by the existing Python engine.</p></div>
        <label className="switch"><input type="checkbox" checked={sample} onChange={(event) => toggleSample(event.target.checked)} /><span /><b>Sample data</b></label>
      </div>
      <Card className="scenario-picker">
        <label htmlFor="example-scenario"><span>Example scenario</span><select id="example-scenario" value={scenarioId} onChange={(event) => { const value = event.target.value as ScenarioSelection; if (value !== "custom") loadScenario(scenariosById[value]); }}><option value="custom">Custom inputs</option>{exampleScenarios.map((scenario) => <option key={scenario.id} value={scenario.id}>{scenario.label}</option>)}</select></label>
        <div><strong>{selectedScenario?.label || "Custom inputs"}</strong><p>{selectedScenario?.description || "Edit or upload your own benchmark evidence, directions, and policy."}</p></div>
      </Card>
      <div className="upload-grid">
        <JsonUpload label="Baseline" hint="Reference benchmark metrics" value={baseline} fileName={names.baseline} onInputStart={invalidateAnalysis} onChange={(value, name) => { invalidateAnalysis(); markCustom(); setBaseline(value); setNames((old) => ({ ...old, baseline: name || "" })); }} />
        <JsonUpload label="Current" hint="Candidate benchmark metrics" value={current} fileName={names.current} onInputStart={invalidateAnalysis} onChange={(value, name) => { invalidateAnalysis(); markCustom(); setCurrent(value); setNames((old) => ({ ...old, current: name || "" })); }} />
        <JsonUpload optional label="Directions" hint="Per-metric regression semantics" value={directions} fileName={names.directions} onInputStart={invalidateAnalysis} onChange={(value, name) => { invalidateAnalysis(); markCustom(); setDirections(value); setNames((old) => ({ ...old, directions: name || "" })); }} />
      </div>
      <Card className="json-guidance">
        <div className="guidance-copy"><span className="eyebrow">Need example JSON?</span><h3>Inspect or save the evidence</h3><p>Choose a scenario above, download the current inputs, or browse the committed files in <code>examples/scenarios/</code>. PR #20 files are permanent snapshots of real GitHub Actions benchmark evidence.</p></div>
        <div className="guidance-actions"><a className="secondary-action" href={SCENARIOS_GITHUB_URL} target="_blank" rel="noreferrer">View JSON on GitHub <ExternalLink size={14} /></a><DownloadButton label="Download baseline" value={baseline} filename="baseline.json" disabled={!downloadable.baseline} /><DownloadButton label="Download current" value={current} filename="current.json" disabled={!downloadable.current} /><DownloadButton label="Download directions" value={directions} filename="directions.json" disabled={!downloadable.directions} /></div>
        {selectedScenario?.pullRequestUrl && <div className="real-evidence"><strong>Real repository evidence</strong><a href={selectedScenario.pullRequestUrl} target="_blank" rel="noreferrer">PR #20 <ExternalLink size={13} /></a>{selectedScenario.workflowUrl && <a href={selectedScenario.workflowUrl} target="_blank" rel="noreferrer">Source workflow <ExternalLink size={13} /></a>}</div>}
      </Card>
      <Card className="controls">
        <div className="threshold-control"><label><span>Regression threshold</span><div className="number-input"><input aria-describedby="threshold-help" type="number" min="0" max="10000" step="0.5" value={threshold} onChange={(event) => { invalidateAnalysis(); markCustom(); setThreshold(event.target.valueAsNumber); }} /><b>%</b></div></label><p id="threshold-help">A metric is flagged when its harmful change reaches or exceeds this percentage. Lower thresholds catch smaller regressions; higher thresholds report only larger changes.</p>{(scenarioId === "standard" || scenarioId === "material") && <small>At 10%: latency_ms and throughput_rps are flagged. At 25%: only latency_ms is flagged.</small>}<small>The dashboard default is 10%; a repository or CI workflow may enforce another policy. This repository&apos;s protected PR gate uses 25%.</small></div>
        <label><span>Fallback direction</span><select value={fallback} onChange={(event) => { const direction = event.target.value; if (isDirection(direction)) { invalidateAnalysis(); markCustom(); setFallback(direction); } }}><option value="higher_is_worse">Higher is worse</option><option value="lower_is_worse">Lower is worse</option></select></label>
        <Button disabled={!valid || loading} onClick={() => void analyze()}>{loading ? <span className="spinner" /> : <Play size={17} />}{loading ? "Analyzing…" : "Run Benchmark Analysis"}</Button>
        <button className="reset" type="button" onClick={() => toggleSample(true)}><RotateCcw size={15} /> Reset sample</button>
      </Card>
      {error && <div className="error-banner" role="alert"><AlertText />{error}</div>}
      <div ref={resultsArea}>{result ? <Results result={result} /> : <EmptyResults />}</div>
      <PrReplay loading={loading} status={replayStatus} onReplay={replay} />
    </section>
  );
}

function AlertText() { return <strong>Unable to run analysis.</strong>; }

function isJsonObject(value: string) {
  try { const parsed: unknown = JSON.parse(value); return Boolean(parsed) && !Array.isArray(parsed) && typeof parsed === "object"; }
  catch { return false; }
}

function DownloadButton({ label, value, filename, disabled }: { label: string; value: string; filename: string; disabled: boolean }) {
  function download() {
    if (disabled) return;
    const url = URL.createObjectURL(new Blob([value], { type: "application/json" }));
    const anchor = document.createElement("a"); anchor.href = url; anchor.download = filename; anchor.click();
    setTimeout(() => URL.revokeObjectURL(url), 0);
  }
  return <button className="secondary-action" type="button" disabled={disabled} aria-label={`${label} JSON`} onClick={download}><Download size={14} />{label}</button>;
}
