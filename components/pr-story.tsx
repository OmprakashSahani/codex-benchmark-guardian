import { ArrowRight, Bot, CheckCircle2, ExternalLink, Gauge, GitPullRequest, ShieldAlert, Wrench } from "lucide-react";

const pr = "https://github.com/OmprakashSahani/codex-benchmark-guardian/pull/20";
const stageOne = "https://github.com/OmprakashSahani/codex-benchmark-guardian/actions/runs/29634627579";
const stageTwo = "https://github.com/OmprakashSahani/codex-benchmark-guardian/actions/runs/29635217444";

export function PrStory() {
  return <section className="proof-section" aria-labelledby="proof-title"><div className="proof-intro"><span className="eyebrow">Documented project example</span><h2 id="proof-title">Proven on a real pull request</h2><p>PR #20 shows the full regression-to-fix loop. This evidence is historical project data—not the current live analysis.</p><a href={pr} target="_blank" rel="noreferrer">View pull request <ExternalLink size={14} /></a></div>
    <div className="proof-card">
      <div className="proof-stages"><article className="proof-stage stage-review"><header><span><ShieldAlert size={18} /></span><div><small>Stage 1 · detected</small><h3>Needs Review</h3></div><strong>70<small>/100</small></strong></header><dl><div><dt>Metric</dt><dd>pr_gate_generation_latency_ms</dd></div><div><dt>Baseline</dt><dd>1.1398080400000001 ms</dd></div><div><dt>Regressed</dt><dd>2.6809987000000004 ms</dd></div><div><dt>Change</dt><dd>+135.21% · critical</dd></div></dl><a href={stageOne} target="_blank" rel="noreferrer">Source workflow <ExternalLink size={13} /></a></article>
        <ArrowRight className="stage-arrow" aria-hidden="true" />
        <article className="proof-stage stage-ready"><header><span><CheckCircle2 size={18} /></span><div><small>Stage 2 · verified</small><h3>Ready</h3></div><strong>100<small>/100</small></strong></header><div className="resolved"><Gauge size={22} /><div><strong>0 regressions</strong><span>Same pull request, optimized and re-evaluated</span></div></div><a href={stageTwo} target="_blank" rel="noreferrer">Source workflow <ExternalLink size={13} /></a></article></div>
      <ol className="proof-timeline"><li><span><GitPullRequest size={15} /></span><b>Regression detected</b></li><li><span><Bot size={15} /></span><b>Codex handoff generated</b></li><li><span><Wrench size={15} /></span><b>Implementation optimized</b></li><li><span><CheckCircle2 size={15} /></span><b>Same PR updated to Ready</b></li></ol>
    </div></section>;
}
