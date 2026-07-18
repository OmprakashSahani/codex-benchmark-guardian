"use client";

import { Play, RotateCcw } from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { sampleBaseline, sampleCurrent, sampleDirections } from "@/lib/sample-data";
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
  const [baseline, setBaseline] = useState(pretty(sampleBaseline));
  const [current, setCurrent] = useState(pretty(sampleCurrent));
  const [directions, setDirections] = useState(pretty(sampleDirections));
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

  function toggleSample(enabled: boolean) {
    invalidateAnalysis(); setSample(enabled); setNames({});
    if (enabled) { setBaseline(pretty(sampleBaseline)); setCurrent(pretty(sampleCurrent)); setDirections(pretty(sampleDirections)); }
    else { setBaseline(""); setCurrent(""); setDirections(""); }
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
    setBaseline(nextBaseline); setCurrent(nextCurrent); setDirections(nextDirections); setThreshold(fixture.threshold); setFallback(fixture.fallbackDirection); setNames({}); setSample(false);
    const message = fixture.kind === "regression" ? "Regression snapshot analyzed live" : "Verified fix snapshot analyzed live";
    void runAnalysis({ baseline: parseMetrics(nextBaseline), current: parseMetrics(nextCurrent), threshold_percent: fixture.threshold, fallback_direction: fixture.fallbackDirection, directions: parseDirections(nextDirections), use_sample_data: false }, message);
  }

  return (
    <section className="workspace" id="analysis">
      <div className="section-heading workspace-heading"><div><span className="eyebrow">Analysis workspace</span><h2>Compare benchmark evidence</h2><p>Inputs stay in memory and are evaluated by the existing Python engine.</p></div>
        <label className="switch"><input type="checkbox" checked={sample} onChange={(event) => toggleSample(event.target.checked)} /><span /><b>Sample data</b></label>
      </div>
      <div className="upload-grid">
        <JsonUpload label="Baseline" hint="Reference benchmark metrics" value={baseline} fileName={names.baseline} onInputStart={invalidateAnalysis} onChange={(value, name) => { invalidateAnalysis(); setBaseline(value); setNames((old) => ({ ...old, baseline: name || "" })); setSample(false); }} />
        <JsonUpload label="Current" hint="Candidate benchmark metrics" value={current} fileName={names.current} onInputStart={invalidateAnalysis} onChange={(value, name) => { invalidateAnalysis(); setCurrent(value); setNames((old) => ({ ...old, current: name || "" })); setSample(false); }} />
        <JsonUpload optional label="Directions" hint="Per-metric regression semantics" value={directions} fileName={names.directions} onInputStart={invalidateAnalysis} onChange={(value, name) => { invalidateAnalysis(); setDirections(value); setNames((old) => ({ ...old, directions: name || "" })); setSample(false); }} />
      </div>
      <Card className="controls">
        <label><span>Regression threshold</span><div className="number-input"><input type="number" min="0" max="10000" step="0.5" value={threshold} onChange={(event) => { invalidateAnalysis(); setThreshold(event.target.valueAsNumber); }} /><b>%</b></div></label>
        <label><span>Fallback direction</span><select value={fallback} onChange={(event) => { const direction = event.target.value; if (isDirection(direction)) { invalidateAnalysis(); setFallback(direction); } }}><option value="higher_is_worse">Higher is worse</option><option value="lower_is_worse">Lower is worse</option></select></label>
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
