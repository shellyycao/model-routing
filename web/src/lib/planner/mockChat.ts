/**
 * Deterministic MOCK chat assistant. No network, no model calls.
 *
 * Understands a few command shapes and turns them into typed GraphEditActions:
 *   add <stage> [after|before <stage>]   ·   add a parallel branch [to <stage>]
 *   remove <stage>   ·   rename <stage> to <name>   ·   connect <stage> to <stage>
 *   review / audit   ·   anything else -> a plain summary of the graph
 * It never cites benchmark numbers and never claims anything was executed.
 */
import { auditWorkflow } from "../auditor/audit";
import { modelLabel } from "../models";
import { applyEdits, diffWorkflows, summarizeDiff, type GraphEditAction } from "../workflow/edits";
import { incoming, outgoing } from "../workflow/graph";
import { makeNode, type TaskType, type Workflow, type WorkflowNode } from "../workflow/schema";
import { MOCK_CHAT_LABEL, type ChatProvider, type ChatRequest, type ChatResponse, type EditProposal } from "./types";

const STOP = new Set(["a", "an", "the", "stage", "step", "node", "my", "this", "new"]);

function tokens(s: string): string[] {
  return s
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, " ")
    .split(/\s+/)
    .filter((t) => t && !STOP.has(t))
    .map((t) => t.replace(/(ing|ed|es|s)$/, "").replace(/(.)\1$/, "$1"));
}

/** Best-matching node by token overlap; null when nothing overlaps. */
export function findNode(w: Workflow, phrase: string): WorkflowNode | null {
  const q = tokens(phrase);
  if (!q.length) return null;
  let best: WorkflowNode | null = null;
  let bestScore = 0;
  for (const n of w.nodes) {
    if (n.name.toLowerCase() === phrase.trim().toLowerCase()) return n;
    const nt = new Set(tokens(n.name));
    const score = q.filter((t) => nt.has(t)).length / Math.max(q.length, nt.size);
    if (score > bestScore) {
      best = n;
      bestScore = score;
    }
  }
  return bestScore > 0 ? best : null;
}

export function guessTaskType(name: string): TaskType {
  const n = name.toLowerCase();
  const rules: [string[], TaskType][] = [
    [["fair", "bias", "evaluat", "metric", "test"], "evaluation"],
    [["feature", "transform", "encode"], "transformation"],
    [["clean", "dedup", "impute"], "cleaning"],
    [["explain", "shap", "interpret"], "explanation"],
    [["report", "summar", "write"], "reporting"],
    [["visual", "chart", "plot", "analy", "explor"], "analysis"],
    [["review", "verif", "check", "citation"], "review"],
    [["extract", "parse"], "extraction"],
    [["train", "model", "fit"], "modeling"],
    [["search", "retriev", "collect"], "retrieval"],
    [["merge", "combine", "join"], "merge"],
  ];
  for (const [keys, t] of rules) if (keys.some((k) => n.includes(k))) return t;
  return "custom";
}

function titleCase(s: string): string {
  const cleaned = s
    .trim()
    .replace(/^(a|an|the)\s+/i, "")
    .replace(/[.?!]+$/, "");
  return cleaned.charAt(0).toUpperCase() + cleaned.slice(1);
}

function uniqueId(w: Workflow, name: string): string {
  const base = `n_${name.toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_|_$/g, "").slice(0, 32) || "stage"}`;
  const ids = new Set(w.nodes.map((n) => n.id));
  if (!ids.has(base)) return base;
  let i = 2;
  while (ids.has(`${base}_${i}`)) i++;
  return `${base}_${i}`;
}

function freeSpot(w: Workflow, near: { x: number; y: number }): { x: number; y: number } {
  const p = { x: near.x, y: near.y + 170 };
  while (w.nodes.some((n) => Math.abs(n.position.x - p.x) < 200 && Math.abs(n.position.y - p.y) < 110)) p.y += 140;
  return p;
}

function proposal(w: Workflow, actions: GraphEditAction[], summary: string): EditProposal | { error: string } {
  const res = applyEdits(w, actions);
  if (!res.ok) return { error: res.errors.join(" ") };
  const diff = diffWorkflows(w, res.workflow);
  return { summary: `${summary} (${summarizeDiff(diff)})`, actions, diff, validation: res.validation, preview: res.workflow };
}

function describe(w: Workflow, selectedId?: string | null): string {
  if (!w.nodes.length) return "The canvas is empty. Describe a goal in Generate workflow, or ask me to “add a Load data stage”.";
  const entries = w.nodes.filter((n) => incoming(n.id, w.edges).length === 0).map((n) => n.name);
  const terminals = w.nodes.filter((n) => outgoing(n.id, w.edges).length === 0).map((n) => n.name);
  const assigned = w.nodes.filter((n) => n.model !== "unassigned").length;
  let text = `This workflow has ${w.nodes.length} stage(s) and ${w.edges.length} connection(s). It starts at ${entries.join(", ") || "—"} and ends at ${terminals.join(", ") || "—"}. ${assigned}/${w.nodes.length} stages have a model assigned.`;
  const sel = selectedId ? w.nodes.find((n) => n.id === selectedId) : undefined;
  if (sel) {
    text += ` Selected: “${sel.name}” (${sel.taskType}), model: ${modelLabel(sel.model, sel.customModelLabel)}, depends on ${incoming(sel.id, w.edges).length} stage(s).`;
  }
  text += " I can't explain model performance yet: evidence-backed answers arrive with the real assistant.";
  return text;
}

export function interpret(message: string, w: Workflow, selectedId?: string | null): { reply: string; proposal?: EditProposal } {
  const m = message.trim();
  const lower = m.toLowerCase();
  const selected = selectedId ? w.nodes.find((n) => n.id === selectedId) ?? null : null;
  const fail = (why: string) => ({ reply: `I couldn't build that change: ${why}` });

  // review / audit
  if (/\b(review|audit|check (my|this|the) workflow|problems?|issues?)\b/.test(lower) && !/^add\b/.test(lower)) {
    const a = auditWorkflow(w);
    const top = a.structural.slice(0, 4).map((f) => `• ${f.title}: ${f.detail}`).join("\n");
    return {
      reply: `Structural review: ${a.counts.error} error(s), ${a.counts.warning} warning(s), ${a.counts.info} note(s).${top ? `\n${top}` : ""}\nOpen the Review tab for the full list. Evidence-based recommendations: none yet (Unverified).`,
    };
  }

  // rename X to Y
  let r = /^rename\s+(.+?)\s+to\s+(.+)$/i.exec(m);
  if (r) {
    const n = findNode(w, r[1]);
    if (!n) return fail(`no stage matches “${r[1]}”.`);
    const p = proposal(w, [{ type: "updateNode", nodeId: n.id, patch: { name: titleCase(r[2]) } }], `Rename “${n.name}” to “${titleCase(r[2])}”`);
    return "error" in p ? fail(p.error) : { reply: p.summary, proposal: p };
  }

  // remove / delete X
  r = /^(remove|delete)\s+(.+)$/i.exec(m);
  if (r) {
    const n = findNode(w, r[2]);
    if (!n) return fail(`no stage matches “${r[2]}”.`);
    const p = proposal(w, [{ type: "removeNode", nodeId: n.id }], `Remove “${n.name}” and its connections`);
    return "error" in p ? fail(p.error) : { reply: p.summary, proposal: p };
  }

  // connect X to Y
  r = /^connect\s+(.+?)\s+(to|->|→)\s+(.+)$/i.exec(m);
  if (r) {
    const a = findNode(w, r[1]);
    const b = findNode(w, r[3]);
    if (!a || !b) return fail("I need two existing stage names.");
    const p = proposal(w, [{ type: "addEdge", source: a.id, target: b.id }], `Connect “${a.name}” → “${b.name}”`);
    return "error" in p ? fail(p.error) : { reply: p.summary, proposal: p };
  }

  // parallel branch
  r = /^(?:add|create)\s+(?:a\s+)?parallel\s+(.+?)?(?:\s+(?:branch|to|for)\s+(.+))?$/i.exec(m);
  if (r || /parallel branch/.test(lower)) {
    const anchorPhrase = r?.[2];
    const anchor = (anchorPhrase && findNode(w, anchorPhrase)) || selected || w.nodes.find((n) => incoming(n.id, w.edges).length > 0 && outgoing(n.id, w.edges).length > 0) || null;
    if (!anchor) return fail("select a stage (with inputs and outputs) to branch alongside.");
    const rawName = r?.[1] && !/^branch$/i.test(r[1].trim()) ? r[1].replace(/\bbranch\b/i, "").trim() : "";
    const name = rawName ? titleCase(rawName) : "Parallel branch";
    const id = uniqueId(w, name);
    const node = makeNode({ id, name, taskType: guessTaskType(name), description: `Runs in parallel with “${anchor.name}”.`, position: freeSpot(w, anchor.position) });
    const actions: GraphEditAction[] = [{ type: "addNode", node }];
    for (const p of incoming(anchor.id, w.edges)) actions.push({ type: "addEdge", source: p, target: id });
    for (const c of outgoing(anchor.id, w.edges)) actions.push({ type: "addEdge", source: id, target: c });
    const p = proposal(w, actions, `Add “${name}” in parallel with “${anchor.name}”`);
    return "error" in p ? fail(p.error) : { reply: p.summary, proposal: p };
  }

  // add X [after|before Y]
  r = /^(?:add|insert|create)\s+(.+?)(?:\s+(after|before)\s+(.+))?$/i.exec(m);
  if (r) {
    const name = titleCase(r[1]);
    const where = r[2]?.toLowerCase();
    const anchor = r[3] ? findNode(w, r[3]) : selected;
    if (r[3] && !anchor) return fail(`no stage matches “${r[3]}”.`);
    const id = uniqueId(w, name);
    const node = makeNode({
      id,
      name,
      taskType: guessTaskType(name),
      description: "",
      position: anchor ? freeSpot(w, anchor.position) : freeSpot(w, { x: 60, y: -90 }),
    });
    const actions: GraphEditAction[] = [{ type: "addNode", node }];
    if (anchor && where === "before") {
      // Insert between anchor's parents and anchor.
      for (const e of w.edges.filter((e) => e.target === anchor.id)) {
        actions.push({ type: "removeEdge", edgeId: e.id }, { type: "addEdge", source: e.source, target: id });
      }
      actions.push({ type: "addEdge", source: id, target: anchor.id });
    } else if (anchor) {
      // After: branch from anchor; feed into the anchor's children that combine results (merge/report/output).
      actions.push({ type: "addEdge", source: anchor.id, target: id });
      const sinks = outgoing(anchor.id, w.edges)
        .flatMap((c) => [c, ...outgoing(c, w.edges)])
        .map((cid) => w.nodes.find((n) => n.id === cid)!)
        .filter((n) => n && ["reporting", "merge", "output"].includes(n.taskType));
      const firstSink = sinks[0];
      if (firstSink) actions.push({ type: "addEdge", source: id, target: firstSink.id });
    }
    const p = proposal(w, actions, anchor ? `Add “${name}” ${where ?? "after"} “${anchor.name}”` : `Add “${name}” as a new stage`);
    return "error" in p ? fail(p.error) : { reply: p.summary, proposal: p };
  }

  return { reply: describe(w, selectedId) };
}

export class MockChatProvider implements ChatProvider {
  readonly kind = "mock" as const;
  constructor(private clock: () => string = () => new Date().toISOString()) {}

  async respond(req: ChatRequest): Promise<ChatResponse> {
    const { reply, proposal } = interpret(req.message ?? "", req.context.workflow, req.context.selectedNodeId);
    return {
      reply,
      proposal,
      provenance: { provider: "mock", label: MOCK_CHAT_LABEL, aiGenerated: false, generatedAt: this.clock() },
    };
  }
}
