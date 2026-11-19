"use client";

import { Handle, Position, type Node, type NodeProps } from "@xyflow/react";
import { memo } from "react";
import { UNASSIGNED, modelLabel } from "@/lib/models";
import { TASK_TYPE_LABELS, type WorkflowNode } from "@/lib/workflow/schema";

export type DiffState = "added" | "modified" | "removed" | null;

export type StageData = {
  stage: WorkflowNode;
  preview: boolean;
  diff: DiffState;
  issue: "error" | "warning" | null;
};

export type StageFlowNode = Node<StageData, "stage">;

const ICONS: Record<string, string> = {
  source: "↧",
  output: "↗",
  merge: "⑃",
  modeling: "✧",
  reporting: "▤",
  evaluation: "✓",
  explanation: "?",
  review: "◎",
};

function StageNodeImpl({ data, selected }: NodeProps<StageFlowNode>) {
  const { stage, preview, diff, issue } = data;
  const border = diff === "added"
    ? "border-dashed border-accent"
    : diff === "removed"
      ? "border-dashed border-danger/70 opacity-55"
      : diff === "modified"
        ? "border-dashed border-warn"
        : preview
          ? "border-dashed border-[#bbaafa]"
          : selected
            ? "border-2 border-[#b39fff] shadow-[0_0_0_4px_#a995ff24,0_12px_26px_#0004]"
            : issue === "error"
              ? "border-danger/80"
              : "border-[#585575] hover:border-[#a89be6]";
  return (
    <div
      className={`w-[208px] rounded-[13px] border bg-card shadow-[0_12px_26px_#0004] ${preview ? "bg-[#2d2944c7]" : ""} ${border}`}
      aria-label={`Stage ${stage.name}, ${TASK_TYPE_LABELS[stage.taskType]}, model ${modelLabel(stage.model, stage.customModelLabel)}${diff ? `, ${diff} in preview` : ""}`}
    >
      <Handle type="target" position={Position.Left} aria-label={`Input of ${stage.name}`} isConnectable={!preview} />
      <div className="flex items-center gap-2.5 px-4 pb-2 pt-3.5">
        <span aria-hidden className="grid h-7 w-7 shrink-0 place-items-center rounded-[9px] bg-[#3a3356] text-sm text-[#cfbeff]">
          {ICONS[stage.taskType] ?? "+"}
        </span>
        <span className="truncate text-sm font-bold" title={stage.name}>
          {stage.name}
        </span>
      </div>
      <div className="px-4 pb-3.5 text-xs">
        <div className="text-soft">{TASK_TYPE_LABELS[stage.taskType]}</div>
        <div className={`mt-0.5 truncate ${stage.model === UNASSIGNED ? "italic text-soft" : "text-[#c6b7f5]"}`}>{modelLabel(stage.model, stage.customModelLabel)}</div>
      </div>
      {diff && (
        <span
          className={`absolute -top-2.5 right-3 rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider ${
            diff === "added" ? "bg-accent text-[#171321]" : diff === "removed" ? "bg-danger text-[#171321]" : "bg-warn text-[#171321]"
          }`}
        >
          {diff}
        </span>
      )}
      {!diff && issue && (
        <span className={`absolute -top-2 right-3 h-3 w-3 rounded-full ${issue === "error" ? "bg-danger" : "bg-warn"}`} title={issue === "error" ? "Has errors — see Review" : "Has warnings — see Review"} />
      )}
      <Handle type="source" position={Position.Right} aria-label={`Output of ${stage.name}`} isConnectable={!preview} />
    </div>
  );
}

export const StageNode = memo(StageNodeImpl);
