"use client";

import { useEffect, useState } from "react";
import type { AnalysisResponse } from "@/lib/types";
import { ArtifactViewer, type Artifact } from "./artifact-viewer";

const definitions = [
  ["codex_repair_goal", "Codex repair goal", "Conditional repair or verification goal from the canonical Repair Contract.", "codex_repair_goal.md", "text/markdown;charset=utf-8", "markdown"],
  ["repair_contract_markdown", "Repair Contract", "Canonical repair boundaries and completion conditions in Markdown.", "repair_contract.md", "text/markdown;charset=utf-8", "markdown"],
  ["repair_contract_json", "Repair Contract JSON", "Canonical structured repair boundaries and completion conditions.", "repair_contract.json", "application/json;charset=utf-8", "json"],
  ["markdown_report", "Benchmark report", "Complete benchmark findings in Markdown.", "benchmark-report.md", "text/markdown;charset=utf-8", "markdown"],
  ["html_report", "HTML report", "Portable report source for browser viewing.", "benchmark-report.html", "text/html;charset=utf-8", "html"],
  ["codex_fix_prompt", "Codex fix prompt", "Focused implementation context for a Codex coding session.", "codex-fix-prompt.txt", "text/plain;charset=utf-8", "text"],
  ["github_issue", "GitHub issue", "Issue-ready summary of the benchmark regression.", "github-issue.md", "text/markdown;charset=utf-8", "markdown"],
  ["ci_workflow", "CI workflow", "Generated GitHub Actions workflow configuration.", "benchmark-workflow.yml", "text/yaml;charset=utf-8", "yaml"],
  ["release_readiness_markdown", "Release readiness", "Shareable release decision and supporting evidence.", "release-readiness.md", "text/markdown;charset=utf-8", "markdown"],
] as const;

export function HandoffPack({ result }: { result: AnalysisResponse }) {
  const repairRequired = result.repair_contract.repair_required;
  const availableDefinitions = definitions.filter(([key]) => repairRequired || key !== "codex_fix_prompt");
  const artifacts: Artifact[] = availableDefinitions.map(([key, title, description, filename, mime, language]) => ({ key, title, description, filename, mime, language, content: result[key] }));
  const [selected, setSelected] = useState<string>(definitions[0][0]);
  const artifact = artifacts.find((item) => item.key === selected) ?? artifacts[0];

  useEffect(() => {
    if (!repairRequired && selected === "codex_fix_prompt") setSelected(definitions[0][0]);
  }, [repairRequired, selected]);

  return <section aria-labelledby="handoff-title"><div className="detail-heading"><div><span className="eyebrow">Generated artifacts</span><h3 id="handoff-title">Complete Codex Handoff Pack</h3><p>Copy or download the exact text produced by the API. Nothing is sent to another service.</p></div></div>
    <div className="artifact-layout"><div className="artifact-selector" role="group" aria-label="Choose a handoff artifact">{artifacts.map((item) => <button type="button" aria-pressed={item.key === artifact.key} key={item.key} onClick={() => setSelected(item.key)}><span>{item.title}</span><small>{item.filename}</small></button>)}</div><ArtifactViewer artifact={artifact} /></div>
  </section>;
}
