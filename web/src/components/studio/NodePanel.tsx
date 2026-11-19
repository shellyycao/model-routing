"use client";

import { useState } from "react";
import { CUSTOM, MODEL_OPTIONS } from "@/lib/models";
import { MERGE_STRATEGIES, TASK_TYPES, TASK_TYPE_LABELS, type ExecutionConfig, type Workflow, type WorkflowNode } from "@/lib/workflow/schema";

const listToText = (xs: string[]) => xs.join(", ");

/** Local editable copy of a prop that resets when the prop changes (undo, chat edits). */
function useSynced(value: string): [string, (v: string) => void] {
  const [state, setState] = useState(value);
  const [prev, setPrev] = useState(value);
  if (prev !== value) {
    setPrev(value);
    setState(value);
  }
  return [state, setState];
}
const textToList = (s: string) =>
  s
    .split(",")
    .map((x) => x.trim())
    .filter(Boolean);

/**
 * Stage settings. Text fields commit on blur (one undo step per edit);
 * selects commit immediately.
 */
export function NodePanel({
  node,
  workflow,
  onChange,
  onDelete,
}: {
  node: WorkflowNode;
  workflow: Workflow;
  onChange: (patch: Partial<WorkflowNode>) => void;
  onDelete: () => void;
}) {
  const deps = workflow.edges.filter((e) => e.target === node.id).map((e) => workflow.nodes.find((n) => n.id === e.source)?.name ?? e.source);
  const downstream = workflow.edges.filter((e) => e.source === node.id).map((e) => workflow.nodes.find((n) => n.id === e.target)?.name ?? e.target);
  const fanIn = deps.length >= 2;

  return (
    // key resets local state when a different stage is selected
    <NodeForm key={node.id} node={node} deps={deps} downstream={downstream} fanIn={fanIn} onChange={onChange} onDelete={onDelete} />
  );
}

function NodeForm({
  node,
  deps,
  downstream,
  fanIn,
  onChange,
  onDelete,
}: {
  node: WorkflowNode;
  deps: string[];
  downstream: string[];
  fanIn: boolean;
  onChange: (patch: Partial<WorkflowNode>) => void;
  onDelete: () => void;
}) {
  const [name, setName] = useSynced(node.name);
  const [desc, setDesc] = useSynced(node.description);
  const [inputs, setInputs] = useSynced(listToText(node.inputs));
  const [outputs, setOutputs] = useSynced(listToText(node.outputs));
  const [custom, setCustom] = useSynced(node.customModelLabel ?? "");
  const [showExec, setShowExec] = useState(Boolean(node.executionConfig));
  const id = (s: string) => `node-${node.id}-${s}`;

  const commitText = (field: "name" | "description", value: string) => {
    const v = field === "name" ? value.trim() || "Untitled stage" : value;
    if (v !== node[field]) onChange({ [field]: v });
  };
  const exec = node.executionConfig ?? {};
  const setExec = (patch: Partial<ExecutionConfig>) => {
    const next = { ...exec, ...patch };
    if (JSON.stringify(next) !== JSON.stringify(exec)) onChange({ executionConfig: next });
  };
  const num = (s: string) => {
    const n = Number(s);
    return s.trim() === "" || !Number.isFinite(n) ? undefined : n;
  };

  return (
    <form className="space-y-5" onSubmit={(e) => e.preventDefault()}>
      <div>
        <label className="field-label" htmlFor={id("name")}>
          Name
        </label>
        <input id={id("name")} className="field-input" value={name} onChange={(e) => setName(e.target.value)} onBlur={() => commitText("name", name)} />
      </div>
      <div>
        <label className="field-label" htmlFor={id("desc")}>
          Description
        </label>
        <textarea id={id("desc")} className="field-input min-h-20 resize-y" value={desc} onChange={(e) => setDesc(e.target.value)} onBlur={() => commitText("description", desc)} />
      </div>
      <div>
        <label className="field-label" htmlFor={id("type")}>
          Task type
        </label>
        <select id={id("type")} className="field-input" value={node.taskType} onChange={(e) => onChange({ taskType: e.target.value as WorkflowNode["taskType"] })}>
          {TASK_TYPES.map((t) => (
            <option key={t} value={t}>
              {TASK_TYPE_LABELS[t]}
            </option>
          ))}
        </select>
      </div>
      <div>
        <label className="field-label" htmlFor={id("model")}>
          Assigned model
        </label>
        <select id={id("model")} className="field-input" value={node.model} onChange={(e) => onChange({ model: e.target.value })}>
          {MODEL_OPTIONS.map((m) => (
            <option key={m.id} value={m.id}>
              {m.label}
            </option>
          ))}
        </select>
        <p className="mt-1.5 text-[11px] leading-snug text-soft">
          Only models tested in this project are listed. A tested model is still <strong>Unverified</strong> for this stage — see the Evidence tab.
        </p>
        {node.model === CUSTOM && (
          <div className="mt-3">
            <label className="field-label" htmlFor={id("custom")}>
              Custom model name (unverified)
            </label>
            <input
              id={id("custom")}
              className="field-input"
              value={custom}
              onChange={(e) => setCustom(e.target.value)}
              onBlur={() => custom !== (node.customModelLabel ?? "") && onChange({ customModelLabel: custom })}
            />
          </div>
        )}
      </div>
      <div>
        <label className="field-label" htmlFor={id("in")}>
          Inputs required (comma-separated)
        </label>
        <input
          id={id("in")}
          className="field-input"
          value={inputs}
          placeholder="e.g. clean data"
          onChange={(e) => setInputs(e.target.value)}
          onBlur={() => listToText(node.inputs) !== listToText(textToList(inputs)) && onChange({ inputs: textToList(inputs) })}
        />
      </div>
      <div>
        <label className="field-label" htmlFor={id("out")}>
          Outputs produced (comma-separated)
        </label>
        <input
          id={id("out")}
          className="field-input"
          value={outputs}
          placeholder="e.g. metrics, report"
          onChange={(e) => setOutputs(e.target.value)}
          onBlur={() => listToText(node.outputs) !== listToText(textToList(outputs)) && onChange({ outputs: textToList(outputs) })}
        />
      </div>
      {fanIn && (
        <div>
          <label className="field-label" htmlFor={id("merge")}>
            How are the {deps.length} inputs combined?
          </label>
          <select
            id={id("merge")}
            className="field-input"
            value={node.mergeStrategy ?? "unspecified"}
            onChange={(e) => onChange({ mergeStrategy: e.target.value as WorkflowNode["mergeStrategy"] })}
          >
            {MERGE_STRATEGIES.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>
        </div>
      )}
      <div className="text-xs leading-relaxed text-muted">
        <p>
          <span className="text-soft">Depends on:</span> {deps.length ? deps.join(", ") : "nothing (entry stage)"}
        </p>
        <p>
          <span className="text-soft">Feeds:</span> {downstream.length ? downstream.join(", ") : "nothing (terminal stage)"}
        </p>
      </div>
      <div className="border-t border-line pt-4">
        <button type="button" className="btn-text text-sm" aria-expanded={showExec} onClick={() => setShowExec((s) => !s)}>
          {showExec ? "▾" : "▸"} Execution config (optional)
        </button>
        {showExec && (
          <div className="mt-3 grid grid-cols-2 gap-3">
            <div>
              <label className="field-label" htmlFor={id("tok")}>
                Max output tokens
              </label>
              <input key={`tok-${exec.maxOutputTokens ?? ""}`} id={id("tok")} type="number" min={1} className="field-input" defaultValue={exec.maxOutputTokens ?? ""} onBlur={(e) => setExec({ maxOutputTokens: num(e.target.value) })} />
            </div>
            <div>
              <label className="field-label" htmlFor={id("temp")}>
                Temperature
              </label>
              <input key={`temp-${exec.temperature ?? ""}`} id={id("temp")} type="number" step={0.1} min={0} max={2} className="field-input" defaultValue={exec.temperature ?? ""} onBlur={(e) => setExec({ temperature: num(e.target.value) })} />
            </div>
            <div>
              <label className="field-label" htmlFor={id("timeout")}>
                Timeout (s)
              </label>
              <input key={`timeout-${exec.timeoutSeconds ?? ""}`} id={id("timeout")} type="number" min={1} className="field-input" defaultValue={exec.timeoutSeconds ?? ""} onBlur={(e) => setExec({ timeoutSeconds: num(e.target.value) })} />
            </div>
            <div className="col-span-2">
              <label className="field-label" htmlFor={id("notes")}>
                Notes
              </label>
              <input key={`notes-${exec.notes ?? ""}`} id={id("notes")} className="field-input" defaultValue={exec.notes ?? ""} onBlur={(e) => setExec({ notes: e.target.value || undefined })} />
            </div>
            <p className="col-span-2 text-[11px] text-soft">Stored with the design only. ModelFlow does not execute workflows.</p>
          </div>
        )}
      </div>
      <div className="flex justify-end border-t border-line pt-4">
        <button type="button" className="btn-ghost hover:text-danger" onClick={onDelete}>
          Delete stage
        </button>
      </div>
    </form>
  );
}
