import { CheckCircle2, ExternalLink, Play, ShieldAlert } from "lucide-react";
import { PR_20_URL, PR_REGRESSION_REPLAY, PR_VERIFIED_FIX_REPLAY, type PrReplayFixture } from "@/lib/pr-demo";
import { Button } from "./ui";

interface PrReplayProps {
  loading: boolean;
  status: string;
  onReplay: (fixture: PrReplayFixture) => void;
}

export function PrReplay({ loading, status, onReplay }: PrReplayProps) {
  return <section className="replay-section" aria-labelledby="replay-title">
    <div className="replay-intro"><span className="eyebrow">Live verified replay</span><h2 id="replay-title">Try the regression-to-fix loop</h2><p>Replay the exact benchmark snapshots produced by PR #20. Each run is evaluated live by the same Python analysis API used by uploaded benchmarks.</p><strong>Historical benchmark evidence · evaluated live</strong><a href={PR_20_URL} target="_blank" rel="noreferrer">View pull request <ExternalLink size={14} /></a></div>
    <div className="replay-cards">
      <article className="replay-card replay-regression"><header><span><ShieldAlert size={18} /></span><div><small>Regression detected</small><h3>Needs Review</h3></div><strong>70<small>/100</small></strong></header><p>1 critical regression across 4 compared metrics.</p><Button disabled={loading} onClick={() => onReplay(PR_REGRESSION_REPLAY)}>{loading ? <span className="spinner" /> : <Play size={15} />}Replay regression</Button><a href={PR_REGRESSION_REPLAY.workflowUrl} target="_blank" rel="noreferrer">Source workflow <ExternalLink size={13} /></a></article>
      <article className="replay-card replay-fix"><header><span><CheckCircle2 size={18} /></span><div><small>Verified fix</small><h3>Ready</h3></div><strong>100<small>/100</small></strong></header><p>0 regressions across 4 compared metrics.</p><Button disabled={loading} onClick={() => onReplay(PR_VERIFIED_FIX_REPLAY)}>{loading ? <span className="spinner" /> : <Play size={15} />}Replay verified fix</Button><a href={PR_VERIFIED_FIX_REPLAY.workflowUrl} target="_blank" rel="noreferrer">Source workflow <ExternalLink size={13} /></a></article>
    </div>
    <p className="replay-status" role="status" aria-live="polite">{status}</p>
  </section>;
}
