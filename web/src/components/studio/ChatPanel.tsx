"use client";

import { useEffect, useRef, useState } from "react";
import { requestChat } from "@/lib/client/session";
import type { GraphEditAction } from "@/lib/workflow/edits";
import type { Workflow } from "@/lib/workflow/schema";

interface Msg {
  role: "user" | "bot";
  text: string;
  label?: string;
}

const QUICK = [
  { label: "+ Fairness check", text: "Add a fairness evaluation after model training" },
  { label: "+ Feature engineering", text: "Add feature engineering before model training" },
  { label: "+ Parallel branch", text: "Add a parallel branch" },
  { label: "Review workflow", text: "Review my workflow" },
];

export function ChatPanel({
  workflow,
  selectedNodeId,
  previewActive,
  onProposal,
}: {
  workflow: Workflow;
  selectedNodeId: string | null;
  previewActive: boolean;
  /** Returns an error string if the proposal could not be previewed. */
  onProposal: (actions: GraphEditAction[], summary: string, label: string) => string | null;
}) {
  const [msgs, setMsgs] = useState<Msg[]>([
    {
      role: "bot",
      text: "Ask me to add, remove, rename or connect stages, or to review the workflow. I propose changes on the canvas; nothing changes until you click Apply.",
      label: "Rule-based assistant (mock) — not AI-generated yet",
    },
  ]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight });
  }, [msgs]);

  const send = async (message: string) => {
    const m = message.trim();
    if (!m || busy) return;
    setMsgs((x) => [...x, { role: "user", text: m }]);
    setText("");
    setBusy(true);
    try {
      const r = await requestChat(m, { page: "studio", workflow, selectedNodeId });
      let reply = r.reply;
      if (r.proposal) {
        if (previewActive) {
          reply += "\n\nFinish or discard the current preview first, then ask again.";
        } else {
          const err = onProposal(r.proposal.actions, r.proposal.summary, r.provenance.label);
          reply += err ? `\n\nThe proposal could not be previewed: ${err}` : "\n\nPreview is on the canvas — Apply, Edit or Discard it there.";
        }
      }
      setMsgs((x) => [...x, { role: "bot", text: reply, label: r.provenance.label }]);
    } catch (e) {
      setMsgs((x) => [...x, { role: "bot", text: `Something went wrong: ${(e as Error).message}` }]);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div ref={listRef} className="flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto py-2" role="log" aria-live="polite" aria-label="Conversation">
        {msgs.map((m, i) =>
          m.role === "user" ? (
            <div key={i} className="max-w-[88%] self-end whitespace-pre-wrap rounded-[14px] bg-[#303047] px-3.5 py-2.5 text-sm text-[#eeebff]">
              {m.text}
            </div>
          ) : (
            <div key={i} className="max-w-[96%] self-start text-sm leading-relaxed text-[#d6d2e7]">
              <p className="whitespace-pre-wrap">{m.text}</p>
              {m.label && <p className="mt-1 text-[10.5px] uppercase tracking-wider text-soft">{m.label}</p>}
            </div>
          ),
        )}
        {busy && <p className="text-xs text-soft">Thinking (rule-based)…</p>}
      </div>
      <div className="flex flex-wrap gap-1.5 pt-2" aria-label="Quick requests">
        {QUICK.map((q) => (
          <button key={q.label} type="button" onClick={() => send(q.text)} className="rounded-full border border-[#49455f] px-2.5 py-1.5 text-[11px] text-[#c8bdeb] hover:border-accent" disabled={busy}>
            {q.label}
          </button>
        ))}
      </div>
      <form
        className="mt-3 rounded-[14px] border border-[#605777] bg-[#212232] p-3 focus-within:border-accent"
        onSubmit={(e) => {
          e.preventDefault();
          send(text);
        }}
      >
        <label htmlFor="chat-input" className="sr-only">
          Message to ModelFlow
        </label>
        <textarea
          id="chat-input"
          rows={3}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              send(text);
            }
          }}
          placeholder="e.g. add outlier removal before train model"
          className="w-full resize-none bg-transparent text-sm leading-normal text-[#f5f2ff] outline-none placeholder:text-soft"
        />
        <div className="flex items-center justify-between gap-2">
          <span className="text-[11px] text-[#9994af]">Preview first · no AI calls</span>
          <button type="submit" className="btn-primary px-3.5 py-2 text-xs" disabled={busy || !text.trim()}>
            Send
          </button>
        </div>
      </form>
    </div>
  );
}
