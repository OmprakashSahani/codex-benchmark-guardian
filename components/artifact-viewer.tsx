"use client";

import { Check, Clipboard, Download, FileText } from "lucide-react";
import { useEffect, useRef, useState } from "react";

export interface Artifact { key: string; title: string; description: string; filename: string; mime: string; language: string; content: string; }

async function copyText(content: string) {
  if (navigator.clipboard?.writeText) return navigator.clipboard.writeText(content);
  const area = document.createElement("textarea");
  area.value = content; area.setAttribute("readonly", ""); area.style.position = "fixed"; area.style.opacity = "0";
  document.body.appendChild(area); area.select();
  try { if (!document.execCommand("copy")) throw new Error("Copy command was unavailable."); } finally { area.remove(); }
}

export function ArtifactViewer({ artifact, copyLabel = "Copy", downloadLabel = "Download" }: { artifact: Artifact; copyLabel?: string; downloadLabel?: string }) {
  const [feedback, setFeedback] = useState("");
  const timeout = useRef<ReturnType<typeof setTimeout> | null>(null);
  const mounted = useRef(true);
  const operationGeneration = useRef(0);
  const currentArtifact = useRef({ key: artifact.key, content: artifact.content });
  currentArtifact.current = { key: artifact.key, content: artifact.content };

  function clearFeedbackTimeout() {
    if (timeout.current) clearTimeout(timeout.current);
    timeout.current = null;
  }

  useEffect(() => {
    operationGeneration.current += 1;
    clearFeedbackTimeout();
    setFeedback("");
  }, [artifact.key, artifact.content]);

  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      operationGeneration.current += 1;
      clearFeedbackTimeout();
    };
  }, []);

  function beginOperation() {
    operationGeneration.current += 1;
    clearFeedbackTimeout();
    return operationGeneration.current;
  }

  function isCurrent(token: number, key: string, content: string) {
    return mounted.current && token === operationGeneration.current
      && key === currentArtifact.current.key && content === currentArtifact.current.content;
  }

  function announce(message: string, token: number, key: string, content: string) {
    if (!isCurrent(token, key, content)) return;
    setFeedback(message);
    clearFeedbackTimeout();
    const handle = setTimeout(() => {
      if (isCurrent(token, key, content) && timeout.current === handle) {
        timeout.current = null;
        setFeedback("");
      }
    }, 3000);
    timeout.current = handle;
  }

  async function copy() {
    const { key, content, title } = artifact;
    const token = beginOperation();
    try {
      await copyText(content);
      announce(`${title} copied.`, token, key, content);
    } catch {
      announce(`Could not copy ${title}. Select the preview text and copy it manually.`, token, key, content);
    }
  }
  function download() {
    const { key, content } = artifact;
    const token = beginOperation();
    try { const url = URL.createObjectURL(new Blob([content], { type: artifact.mime })); const link = document.createElement("a"); link.href = url; link.download = artifact.filename; document.body.appendChild(link); link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(url), 0); announce(`${artifact.filename} download started.`, token, key, content); }
    catch { announce(`Could not download ${artifact.filename}.`, token, key, content); }
  }
  return <article className="artifact-viewer"><header><div className="artifact-heading"><span><FileText size={18} /></span><div><h4>{artifact.title}</h4><p>{artifact.description}</p></div></div><div className="artifact-actions"><button type="button" onClick={() => void copy()}>{feedback.includes("copied") ? <Check size={15} /> : <Clipboard size={15} />}{copyLabel}</button><button type="button" onClick={download}><Download size={15} />{downloadLabel}</button></div></header><div className="code-label"><span>{artifact.filename}</span><span>{artifact.language}</span></div><pre tabIndex={0} aria-label={`${artifact.title} text preview`}><code>{artifact.content}</code></pre><p className="sr-only" role="status" aria-live="polite">{feedback}</p></article>;
}
