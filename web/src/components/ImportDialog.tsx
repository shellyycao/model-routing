"use client";

import { useEffect, useId, useRef, useState } from "react";
import { importWorkflowText } from "@/lib/workflow/io";
import type { Workflow } from "@/lib/workflow/schema";
import { validateWorkflow } from "@/lib/workflow/validate";

const PLACEHOLDER = `{
  "schemaVersion": 1,
  "name": "My flow",
  "nodes": [
    { "id": "collect", "name": "Collect", "position": { "x": 80, "y": 140 } },
    { "id": "analyze", "name": "Analyze", "position": { "x": 380, "y": 140 } }
  ],
  "edges": [{ "source": "collect", "target": "analyze" }]
}`;

export function ImportDialog({
  open,
  onClose,
  onImport,
  fallbackId,
}: {
  open: boolean;
  onClose: () => void;
  onImport: (w: Workflow, warnings: string[], sourceName: string) => void;
  fallbackId: string;
}) {
  const [text, setText] = useState("");
  const [fileName, setFileName] = useState("pasted text");
  const [errors, setErrors] = useState<string[]>([]);
  const titleId = useId();
  const ref = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const d = ref.current;
    if (!d) return;
    if (open && !d.open) d.showModal();
    if (!open && d.open) d.close();
  }, [open]);

  const submit = () => {
    const r = importWorkflowText(text, { fallbackId });
    if (!r.ok) {
      setErrors(r.errors);
      return;
    }
    const v = validateWorkflow(r.workflow);
    const errs = v.issues.filter((i) => i.severity === "error").map((i) => i.message);
    if (errs.length) {
      setErrors(["The workflow has structural errors and cannot be previewed:", ...errs]);
      return;
    }
    setErrors([]);
    setText("");
    onImport({ ...r.workflow, meta: { ...r.workflow.meta, origin: "import" } }, [...r.warnings, ...v.issues.map((i) => i.message)], fileName);
  };

  return (
    <dialog
      ref={ref}
      aria-labelledby={titleId}
      onClose={onClose}
      onCancel={onClose}
      className="m-auto w-[min(600px,calc(100vw-32px))] rounded-2xl border border-[#5c5475] bg-[#1a1b29] p-7 text-ink backdrop:bg-black/60"
    >
      <h2 id={titleId} className="mb-2 text-2xl font-semibold">
        Import a workflow
      </h2>
      <p className="mb-4 text-sm leading-relaxed text-[#a9a5bc]">
        Paste a ModelFlow JSON or YAML definition, or choose a file. You will review it on the canvas before anything is applied.
      </p>
      <label className="field-label" htmlFor={`${titleId}-file`}>
        File (.json, .yaml, .yml)
      </label>
      <input
        id={`${titleId}-file`}
        type="file"
        accept=".json,.yaml,.yml,application/json,text/yaml"
        className="mb-4 block text-sm text-muted file:mr-3 file:rounded-md file:border-0 file:bg-[#292a3b] file:px-3 file:py-2 file:text-ink"
        onChange={async (e) => {
          const f = e.target.files?.[0];
          if (!f) return;
          setFileName(f.name);
          setText(await f.text());
        }}
      />
      <label className="field-label" htmlFor={`${titleId}-text`}>
        Definition
      </label>
      <textarea
        id={`${titleId}-text`}
        value={text}
        onChange={(e) => {
          setText(e.target.value);
          setFileName("pasted text");
        }}
        placeholder={PLACEHOLDER}
        spellCheck={false}
        className="h-48 w-full resize-y rounded-[10px] border border-[#4d4b60] bg-[#10121b] p-3 font-mono text-xs text-[#eeeaf5] outline-none focus:border-accent"
      />
      {errors.length > 0 && (
        <ul role="alert" className="mt-3 space-y-1 text-sm text-danger">
          {errors.map((e, i) => (
            <li key={i}>{e}</li>
          ))}
        </ul>
      )}
      <div className="mt-4 flex justify-end gap-2">
        <button type="button" className="btn-secondary" onClick={onClose}>
          Cancel
        </button>
        <button type="button" className="btn-primary" onClick={submit} disabled={!text.trim()}>
          Preview import →
        </button>
      </div>
    </dialog>
  );
}
