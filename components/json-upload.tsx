"use client";

import { CheckCircle2, FileJson, UploadCloud } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Card } from "./ui";

interface JsonUploadProps {
  label: string;
  hint: string;
  value: string;
  fileName?: string;
  optional?: boolean;
  onInputStart?: () => void;
  onChange: (value: string, fileName?: string) => void;
}

export function JsonUpload({ label, hint, value, fileName, optional, onInputStart, onChange }: JsonUploadProps) {
  const input = useRef<HTMLInputElement>(null);
  const readGeneration = useRef(0);
  const [dragging, setDragging] = useState(false);
  const [readError, setReadError] = useState("");

  useEffect(() => () => {
    readGeneration.current += 1;
  }, []);

  let error = "";
  if (value.trim()) {
    try {
      const parsed = JSON.parse(value);
      if (!parsed || Array.isArray(parsed) || typeof parsed !== "object") error = "Enter a JSON object.";
    } catch {
      error = "Invalid JSON syntax.";
    }
  } else if (!optional) error = "JSON input is required.";

  async function load(file?: File) {
    if (!file) return;
    const generation = ++readGeneration.current;
    onInputStart?.();
    setReadError("");
    try {
      const content = await file.text();
      if (generation === readGeneration.current) onChange(content, file.name);
    } catch {
      if (generation === readGeneration.current) {
        setReadError("Could not read this file. Choose another JSON file and try again.");
      }
    }
  }

  return (
    <Card className="upload-card">
      <div className="input-heading">
        <div><span className="eyebrow">{optional ? "Optional input" : "Required input"}</span><h3>{label}</h3></div>
        <FileJson size={20} />
      </div>
      <button
        type="button"
        className={`dropzone ${dragging ? "is-dragging" : ""}`}
        onClick={() => input.current?.click()}
        onDragOver={(event) => { event.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={(event) => { event.preventDefault(); setDragging(false); void load(event.dataTransfer.files[0]); }}
      >
        <UploadCloud size={20} />
        <span>{fileName || "Drop JSON here or choose a file"}</span>
        <small>{hint}</small>
      </button>
      <input ref={input} hidden type="file" accept="application/json,.json" onChange={(event) => void load(event.target.files?.[0])} />
      <textarea aria-label={`${label} JSON`} value={value} spellCheck={false} onChange={(event) => { readGeneration.current += 1; setReadError(""); onChange(event.target.value); }} />
      <p className={`validation ${readError || error ? "invalid" : "valid"}`}>
        {readError || error ? readError || error : <><CheckCircle2 size={14} /> Valid JSON object</>}
      </p>
    </Card>
  );
}
