import { ArrowDown, Binary, Bot, Fingerprint } from "lucide-react";
import { AnalysisWorkspace } from "@/components/analysis-workspace";
import { Header } from "@/components/header";
import { PrStory } from "@/components/pr-story";

export default function Home() {
  return <main id="top"><div className="background-grid" /><div className="shell"><Header />
    <section className="hero"><div className="hero-kicker"><span /> Performance confidence for every merge</div><h1>Catch performance regressions <em>before they merge.</em></h1><p>Functional tests can pass while latency climbs, memory grows, and throughput falls. Benchmark Guardian turns those hidden shifts into a deterministic release decision and an actionable Codex handoff.</p>
      <a className="hero-link" href="#analysis">Analyze benchmarks <ArrowDown size={16} /></a>
      <div className="trust"><div><Fingerprint /><span><b>Deterministic analysis</b><small>Repeatable, explainable results</small></span></div><div><Binary /><span><b>Protected evaluator</b><small>Python remains the source of truth</small></span></div><div><Bot /><span><b>Codex-ready handoff</b><small>From signal to focused fix</small></span></div></div>
    </section><AnalysisWorkspace /><PrStory /><footer><span>Codex Benchmark Guardian</span><span>Deterministic evidence for confident releases · OpenAI Build Week</span></footer></div></main>;
}
