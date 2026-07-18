import { CheckCircle2, SearchCheck } from "lucide-react";
import type { TriageNote } from "@/lib/types";

export function TriagePanel({ notes }: { notes: TriageNote[] }) {
  if (!notes.length) return <div className="positive-empty"><span><CheckCircle2 size={25} /></span><h3>No regressions need triage</h3><p>The evaluator returned no triage notes for this comparison.</p></div>;
  return <section aria-labelledby="triage-title"><div className="detail-heading"><div><span className="eyebrow">Investigation guide</span><h3 id="triage-title">Regression triage</h3><p>API-generated context to focus the next engineering pass.</p></div></div>
    <div className="triage-grid">{notes.map((note) => <article className="triage-note" key={note.metric_name}><div className="triage-title"><span><SearchCheck size={18} /></span><div><small>Metric</small><h4>{note.metric_name}</h4></div></div><dl><div><dt>Likely area</dt><dd>{note.likely_area}</dd></div><div><dt>Why it matters</dt><dd>{note.why_it_matters}</dd></div></dl><div className="suggested-checks"><h5>Suggested checks</h5><ul>{note.suggested_checks.map((check) => <li key={check}>{check}</li>)}</ul></div></article>)}</div>
  </section>;
}
