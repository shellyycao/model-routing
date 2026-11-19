"use client";

import {
  Background,
  BackgroundVariant,
  Controls,
  MarkerType,
  ReactFlow,
  ReactFlowProvider,
  applyNodeChanges,
  useReactFlow,
  type Connection,
  type Edge,
  type EdgeChange,
  type IsValidConnection,
  type NodeChange,
  type OnDelete,
} from "@xyflow/react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { EvidencePanel } from "@/components/evidence/EvidencePanel";
import { ImportDialog } from "@/components/ImportDialog";
import { auditWorkflow } from "@/lib/auditor/audit";
import { downloadText, newId, requestPlan, slugify, takePendingDraft } from "@/lib/client/session";
import { MOCK_PLANNER_LABEL } from "@/lib/planner/types";
import { browserStore, type WorkflowStore } from "@/lib/storage/store";
import { exampleParallel, examplePipeline } from "@/lib/workflow/examples";
import { applyEdits, diffWorkflows, summarizeDiff, type GraphEditAction, type WorkflowDiff } from "@/lib/workflow/edits";
import { wouldCreateCycle } from "@/lib/workflow/graph";
import { canRedo, canUndo, commit, createHistory, redo, undo, type History } from "@/lib/workflow/history";
import { exportWorkflowJson, exportWorkflowYaml } from "@/lib/workflow/io";
import { emptyWorkflow, makeNode, type TaskType, type Workflow, type WorkflowNode } from "@/lib/workflow/schema";
import { AuditPanel } from "./AuditPanel";
import { ChatPanel } from "./ChatPanel";
import { NodePanel } from "./NodePanel";
import { StageNode, type DiffState, type StageFlowNode } from "./StageNode";

type PanelTab = "stage" | "review" | "evidence" | "ask";
type PreviewKind = "planner" | "chat" | "import" | "example";

interface Preview {
  kind: PreviewKind;
  workflow: Workflow;
  base: Workflow;
  diff: WorkflowDiff;
  label: string;
  detail: string;
  warnings: string[];
}

const PREVIEW_BROW: Record<PreviewKind, string> = {
  planner: "TEMPLATE DRAFT (MOCK PLANNER) — NOT AI-GENERATED YET · NOT APPLIED",
  chat: "PROPOSED EDIT (MOCK ASSISTANT) · NOT APPLIED",
  import: "IMPORTED WORKFLOW · REVIEW BEFORE APPLYING",
  example: "EXAMPLE PATTERN · NOT APPLIED",
};

const PLANNER_EXAMPLES = [
  { label: "Customer churn", goal: "Predict customer churn, evaluate performance, explain key drivers and write a report." },
  { label: "Literature review", goal: "Review research papers, extract evidence, verify citations and synthesize findings." },
  { label: "Parallel analytics", goal: "Clean my dataset, analyze trends and create visualizations in parallel, then report." },
];

const PALETTE: { type: TaskType; label: string; glyph: string; name: string }[] = [
  { type: "source", label: "Input / source", glyph: "↧", name: "Input" },
  { type: "custom", label: "Task stage", glyph: "+", name: "New stage" },
  { type: "merge", label: "Merge", glyph: "⑃", name: "Merge" },
  { type: "output", label: "Output", glyph: "↗", name: "Output" },
];

const nodeTypes = { stage: StageNode };
const snapshot = (w: Workflow) => JSON.stringify({ ...w, meta: { ...w.meta, updatedAt: "" } });
const isTyping = (t: EventTarget | null) => t instanceof HTMLElement && (t.isContentEditable || ["INPUT", "TEXTAREA", "SELECT"].includes(t.tagName));

export function Studio() {
  return (
    <ReactFlowProvider>
      <StudioInner />
    </ReactFlowProvider>
  );
}

function StudioInner() {
  const params = useSearchParams();
  const rf = useReactFlow();
  const storeRef = useRef<WorkflowStore | null>(null);
  const loadedKey = useRef<string | null>(null);
  const canvasRef = useRef<HTMLDivElement>(null);
  const dragging = useRef(false);

  const [hist, setHist] = useState<History<Workflow>>(() => createHistory(emptyWorkflow("wf_loading")));
  const wf = hist.present;
  const [savedSnap, setSavedSnap] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [selectedEdges, setSelectedEdges] = useState<Set<string>>(new Set());
  const [preview, setPreview] = useState<Preview | null>(null);
  const [tab, setTab] = useState<PanelTab | null>(null);
  const [plannerOpen, setPlannerOpen] = useState(false);
  const [plannerGoal, setPlannerGoal] = useState("");
  const [plannerBusy, setPlannerBusy] = useState(false);
  const [importOpen, setImportOpen] = useState(false);
  const [toast, setToast] = useState<string | null>(null);
  const [rfNodes, setRfNodes] = useState<StageFlowNode[]>([]);
  const [title, setTitle] = useState(wf.name);
  const [prevName, setPrevName] = useState(wf.name);
  if (prevName !== wf.name) {
    setPrevName(wf.name);
    setTitle(wf.name);
  }

  const showToast = useCallback((m: string) => {
    setToast(m);
    window.setTimeout(() => setToast((t) => (t === m ? null : t)), 3800);
  }, []);

  const fitSoon = useCallback(() => window.setTimeout(() => rf.fitView({ padding: 0.25, duration: 250, maxZoom: 1.1 }), 80), [rf]);

  const startPreview = useCallback(
    (kind: PreviewKind, base: Workflow, next: Workflow, label: string, detail: string, warnings: string[] = []) => {
      setPreview({ kind, base, workflow: next, diff: diffWorkflows(base, next), label, detail, warnings });
      setSelectedId(null);
      setSelectedEdges(new Set());
      fitSoon();
    },
    [fitSoon],
  );

  // ---- Load (once per URL) -------------------------------------------------
  useEffect(() => {
    const key = params.toString();
    const id = params.get("id");
    if (loadedKey.current === key) return;
    if (id && loadedKey.current !== null && id === hist.present.id) {
      loadedKey.current = key; // URL updated after first save; nothing to reload
      return;
    }
    loadedKey.current = key;
    const store = storeRef.current ?? browserStore();
    storeRef.current = store;
    // No cancellation: the guard above ensures one load per URL (React StrictMode
    // re-runs effects, and the pending draft can only be taken once).
    (async () => {
      let base = emptyWorkflow(newId("wf"));
      let saved: string | null = null;
      if (id) {
        const w = await store.get(id);
        if (w) {
          base = w;
          saved = snapshot(w);
        } else showToast("That workflow was not found in this browser. Starting a new one.");
      }
      setHist(createHistory(base));
      setSavedSnap(saved);
      setPreview(null);
      setSelectedId(null);
      if (params.get("pending")) {
        const p = takePendingDraft();
        if (p?.kind === "planner") {
          const d = p.response.draft;
          startPreview("planner", base, { ...d, id: base.id, meta: { ...d.meta, createdAt: base.meta.createdAt } }, p.response.provenance.label, p.response.rationale);
        } else if (p?.kind === "import") {
          startPreview("import", base, { ...p.workflow, id: base.id }, `Imported from ${p.sourceName}`, "Check the structure, then apply.", p.warnings);
        }
      }
      if (!params.get("pending") && params.get("new") !== null) setPlannerOpen(false);
      fitSoon();
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params]);

  // ---- Derived -----------------------------------------------------------
  const audit = useMemo(() => auditWorkflow(wf), [wf]);
  const issueByNode = useMemo(() => {
    const m = new Map<string, "error" | "warning">();
    for (const f of audit.structural) {
      if (f.severity === "info") continue;
      for (const id of f.nodeIds) if (m.get(id) !== "error") m.set(id, f.severity);
    }
    return m;
  }, [audit]);
  const dirty = savedSnap === null ? wf.nodes.length > 0 || wf.edges.length > 0 : snapshot(wf) !== savedSnap;
  const selectedNode = wf.nodes.find((n) => n.id === selectedId) ?? null;

  // Build React Flow nodes from the workflow (or preview), preserving measured sizes.
  useEffect(() => {
    let display: { stage: WorkflowNode; diff: DiffState; ghost?: boolean }[];
    if (preview) {
      const added = new Set(preview.diff.addedNodes);
      const modified = new Set(preview.diff.modifiedNodes.map((m) => m.id));
      display = [
        ...preview.workflow.nodes.map((n) => ({ stage: n, diff: (added.has(n.id) ? "added" : modified.has(n.id) ? "modified" : null) as DiffState })),
        ...preview.base.nodes.filter((n) => preview.diff.removedNodes.includes(n.id)).map((n) => ({ stage: n, diff: "removed" as DiffState, ghost: true })),
      ];
    } else {
      display = wf.nodes.map((n) => ({ stage: n, diff: null }));
    }
    // Syncing external graph state into React Flow's node list is the intended use here.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setRfNodes((prev) => {
      const old = new Map(prev.map((n) => [n.id, n]));
      return display.map(({ stage, diff, ghost }) => ({
        id: ghost ? `__removed__${stage.id}` : stage.id,
        type: "stage" as const,
        position: stage.position,
        selected: !preview && stage.id === selectedId,
        draggable: !preview,
        selectable: !preview,
        connectable: !preview,
        deletable: !preview,
        measured: old.get(ghost ? `__removed__${stage.id}` : stage.id)?.measured,
        data: { stage, preview: Boolean(preview), diff, issue: preview ? null : issueByNode.get(stage.id) ?? null },
      }));
    });
  }, [wf, preview, selectedId, issueByNode]);

  const rfEdges: Edge[] = useMemo(() => {
    const marker = (color: string) => ({ type: MarkerType.ArrowClosed, color, width: 18, height: 18 });
    if (preview) {
      const key = (e: { source: string; target: string }) => `${e.source}->${e.target}`;
      const added = new Set(preview.diff.addedEdges.map(key));
      const removedNodes = new Set(preview.diff.removedNodes);
      const removed = preview.diff.removedEdges.map((e) => ({
        id: `__removed__${key(e)}`,
        source: removedNodes.has(e.source) ? `__removed__${e.source}` : e.source,
        target: removedNodes.has(e.target) ? `__removed__${e.target}` : e.target,
        className: "edge-preview-removed",
        selectable: false,
        markerEnd: marker("#f29b9b"),
      }));
      return [
        ...preview.workflow.edges.map((e) => ({
          id: e.id,
          source: e.source,
          target: e.target,
          className: added.has(key(e)) ? "edge-preview-added" : "edge-preview",
          selectable: false,
          markerEnd: marker("#b3a2ff"),
        })),
        ...removed,
      ];
    }
    return wf.edges.map((e) => ({
      id: e.id,
      source: e.source,
      target: e.target,
      selected: selectedEdges.has(e.id),
      markerEnd: marker(selectedEdges.has(e.id) ? "#66cbbd" : "#8779c2"),
      ariaLabel: `Connection from ${wf.nodes.find((n) => n.id === e.source)?.name ?? e.source} to ${wf.nodes.find((n) => n.id === e.target)?.name ?? e.target}`,
    }));
  }, [wf, preview, selectedEdges]);

  // ---- Mutations ---------------------------------------------------------
  const commitWf = useCallback(
    (fn: (w: Workflow) => Workflow) =>
      setHist((h) => {
        const next = fn(h.present);
        return commit(h, { ...next, meta: { ...next.meta, updatedAt: new Date().toISOString() } });
      }),
    [],
  );

  const runEdits = useCallback(
    (actions: GraphEditAction[], failPrefix: string): boolean => {
      const r = applyEdits(hist.present, actions);
      if (!r.ok) {
        showToast(`${failPrefix}: ${r.errors[0]}`);
        return false;
      }
      commitWf(() => r.workflow);
      return true;
    },
    [hist.present, commitWf, showToast],
  );

  const onNodesChange = useCallback(
    (changes: NodeChange<StageFlowNode>[]) => {
      setRfNodes((nds) => applyNodeChanges(changes.filter((c) => c.type !== "remove"), nds));
      for (const c of changes) {
        if (c.type === "select") {
          if (c.selected) setSelectedId(c.id);
          else setSelectedId((cur) => (cur === c.id ? null : cur));
        }
      }
      // Keyboard moves (arrow keys) are not drags: commit them directly.
      const moves = changes.filter((c): c is Extract<NodeChange, { type: "position" }> => c.type === "position" && !!c.position && !c.dragging);
      if (moves.length && !dragging.current) {
        commitWf((w) => ({ ...w, nodes: w.nodes.map((n) => {
          const m = moves.find((x) => x.id === n.id);
          return m?.position ? { ...n, position: { ...m.position } } : n;
        }) }));
      }
    },
    [commitWf],
  );

  const onEdgesChange = useCallback((changes: EdgeChange[]) => {
    setSelectedEdges((cur) => {
      const next = new Set(cur);
      for (const c of changes) {
        if (c.type !== "select") continue;
        if (c.selected) next.add(c.id);
        else next.delete(c.id);
      }
      return next;
    });
  }, []);

  const onDelete: OnDelete = useCallback(
    ({ nodes, edges }) => {
      if (preview) return;
      const nodeIds = new Set(nodes.map((n) => n.id));
      const edgeIds = new Set(edges.map((e) => e.id));
      commitWf((w) => ({
        ...w,
        nodes: w.nodes.filter((n) => !nodeIds.has(n.id)),
        edges: w.edges.filter((e) => !edgeIds.has(e.id) && !nodeIds.has(e.source) && !nodeIds.has(e.target)),
      }));
      if (selectedId && nodeIds.has(selectedId)) setSelectedId(null);
      setSelectedEdges(new Set());
    },
    [preview, commitWf, selectedId],
  );

  const isValidConnection: IsValidConnection = useCallback(
    (c) => !!c.source && !!c.target && c.source !== c.target && !wf.edges.some((e) => e.source === c.source && e.target === c.target) && !wouldCreateCycle(wf.edges, c.source, c.target),
    [wf.edges],
  );

  const onConnect = useCallback(
    (c: Connection) => {
      if (preview || !c.source || !c.target) return;
      if (wouldCreateCycle(hist.present.edges, c.source, c.target)) {
        showToast("That connection would create a cycle. Workflows must be acyclic.");
        return;
      }
      runEdits([{ type: "addEdge", source: c.source, target: c.target }], "Could not connect");
    },
    [preview, hist.present.edges, runEdits, showToast],
  );

  const onReconnect = useCallback(
    (oldEdge: Edge, c: Connection) => {
      if (preview || !c.source || !c.target) return;
      const ok = runEdits(
        [
          { type: "removeEdge", edgeId: oldEdge.id },
          { type: "addEdge", source: c.source, target: c.target },
        ],
        "Could not reconnect",
      );
      if (ok) setSelectedEdges(new Set());
    },
    [preview, runEdits],
  );

  const addStage = (type: TaskType, name: string) => {
    if (preview) return;
    const rect = canvasRef.current?.getBoundingClientRect();
    const center = rect ? rf.screenToFlowPosition({ x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 }) : { x: 100, y: 100 };
    const jitter = (wf.nodes.length % 5) * 24;
    const node = makeNode({ id: newId("n"), name, taskType: type, position: { x: center.x - 104 + jitter, y: center.y - 50 + jitter } });
    commitWf((w) => ({ ...w, nodes: [...w.nodes, node] }));
    setSelectedId(node.id);
    setTab("stage");
  };

  const updateNode = (id: string, patch: Partial<WorkflowNode>) => runEdits([{ type: "updateNode", nodeId: id, patch }], "Could not update stage");

  const deleteNode = (id: string) => {
    runEdits([{ type: "removeNode", nodeId: id }], "Could not delete");
    setSelectedId(null);
  };

  const doUndo = useCallback(() => {
    if (preview) return;
    setHist((h) => undo(h));
  }, [preview]);
  const doRedo = useCallback(() => {
    if (preview) return;
    setHist((h) => redo(h));
  }, [preview]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (isTyping(e.target)) return;
      const mod = e.metaKey || e.ctrlKey;
      if (mod && e.key.toLowerCase() === "z") {
        e.preventDefault();
        if (e.shiftKey) doRedo();
        else doUndo();
      } else if (mod && e.key.toLowerCase() === "y") {
        e.preventDefault();
        doRedo();
      } else if (e.key === "Escape" && preview === null) {
        setPlannerOpen(false);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [doUndo, doRedo, preview]);

  useEffect(() => {
    const onUnload = (e: BeforeUnloadEvent) => {
      if (dirty) e.preventDefault();
    };
    window.addEventListener("beforeunload", onUnload);
    return () => window.removeEventListener("beforeunload", onUnload);
  }, [dirty]);

  // ---- Preview actions -----------------------------------------------------
  const applyPreview = (thenEdit: boolean) => {
    if (!preview) return;
    const next = preview.workflow;
    const firstAdded = preview.diff.addedNodes[0] ?? next.nodes[0]?.id ?? null;
    commitWf(() => next);
    setPreview(null);
    showToast(`Applied (${summarizeDiff(preview.diff)}). Undo is available.`);
    if (thenEdit && firstAdded) {
      setSelectedId(firstAdded);
      setTab("stage");
    }
  };

  const generateFromStudio = async () => {
    if (!plannerGoal.trim()) return;
    setPlannerBusy(true);
    try {
      const r = await requestPlan(plannerGoal);
      setPlannerOpen(false);
      startPreview("planner", hist.present, { ...r.draft, id: hist.present.id, name: hist.present.nodes.length ? hist.present.name : r.draft.name }, r.provenance.label, r.rationale);
    } catch (e) {
      showToast((e as Error).message);
    } finally {
      setPlannerBusy(false);
    }
  };

  const onChatProposal = (actions: GraphEditAction[], summary: string, label: string): string | null => {
    // Re-validate locally against the *current* graph before previewing.
    const r = applyEdits(hist.present, actions);
    if (!r.ok) return r.errors[0];
    startPreview("chat", hist.present, r.workflow, label, summary);
    return null;
  };

  const save = async () => {
    const store = storeRef.current;
    if (!store || preview) return;
    try {
      const v = await store.save(wf, wf.meta.origin === "template-mock" && savedSnap === null ? "First save of template draft" : "");
      setSavedSnap(snapshot(wf));
      showToast(`Saved as version ${v.number} in this browser.`);
      if (params.get("id") !== wf.id) {
        loadedKey.current = `id=${encodeURIComponent(wf.id)}`;
        window.history.replaceState(null, "", `/studio?id=${encodeURIComponent(wf.id)}`);
      }
    } catch (e) {
      showToast(`Save failed: ${(e as Error).message}`);
    }
  };

  const commitTitle = () => {
    const t = title.trim() || "Untitled workflow";
    if (t !== wf.name) commitWf((w) => ({ ...w, name: t }));
    else setTitle(t);
  };

  const focusNode = (id: string) => {
    const n = wf.nodes.find((x) => x.id === id);
    if (!n) return;
    setSelectedId(id);
    rf.setCenter(n.position.x + 104, n.position.y + 50, { zoom: 1.1, duration: 300 });
  };

  const openTab = (t: PanelTab) => setTab((cur) => (cur === t ? null : t));
  const nowIso = () => new Date().toISOString();

  // ---- Render --------------------------------------------------------------
  return (
    <div className="relative flex h-[calc(100dvh-4rem)] min-h-[480px]">
      {/* Left palette: icon rail below lg */}
      <aside aria-label="Add stages and patterns" className="flex w-14 shrink-0 flex-col border-r border-line bg-[#151620] lg:w-56">
        <div className="flex-1 overflow-y-auto px-1.5 py-5 lg:px-3.5">
          <PaletteHeading>Add stage</PaletteHeading>
          {PALETTE.map((p) => (
            <PaletteButton key={p.type} glyph={p.glyph} label={p.label} onClick={() => addStage(p.type, p.name)} disabled={!!preview} />
          ))}
          <div className="mx-2 my-5 h-px bg-line" />
          <PaletteHeading>Try a pattern</PaletteHeading>
          <PaletteButton glyph="⑂" label="Parallel branches" disabled={!!preview} onClick={() => startPreview("example", wf, { ...exampleParallel(nowIso()), id: wf.id }, "Example pattern — models not assigned", "Replaces the canvas with a fan-out / fan-in example.")} />
          <PaletteButton glyph="→" label="Simple pipeline" disabled={!!preview} onClick={() => startPreview("example", wf, { ...examplePipeline(nowIso()), id: wf.id }, "Example pattern — models not assigned", "Replaces the canvas with a linear example.")} />
          <div className="mx-2 my-5 h-px bg-line" />
          <PaletteHeading>Workflow</PaletteHeading>
          <PaletteButton glyph="⇧" label="Import JSON / YAML" disabled={!!preview} onClick={() => setImportOpen(true)} />
          <PaletteButton glyph="↓" label="Export JSON" onClick={() => downloadText(`${slugify(wf.name)}.modelflow.json`, exportWorkflowJson(wf))} />
          <PaletteButton glyph="⤓" label="Export YAML" onClick={() => downloadText(`${slugify(wf.name)}.modelflow.yaml`, exportWorkflowYaml(wf), "text/yaml")} />
          <Link href="/library" className="flex w-full items-center gap-2.5 rounded-[10px] px-2 py-2.5 text-sm text-[#cac8d9] hover:bg-[#272636] hover:text-white" aria-label="My Workflows">
            <Glyph>▤</Glyph>
            <span className="hidden lg:inline">My Workflows</span>
          </Link>
        </div>
        <p className="hidden border-t border-line px-4 py-3.5 text-xs leading-relaxed text-soft lg:block">
          Drag from a stage&apos;s right dot to another stage&apos;s left dot. One output can feed several stages.
        </p>
      </aside>

      {/* Canvas column */}
      <main className="flex min-w-0 flex-1 flex-col" aria-label="Workflow studio">
        <div className="flex flex-wrap items-center justify-between gap-x-3 gap-y-2 border-b border-line px-3 py-2.5 sm:px-6 sm:py-3">
          <div className="min-w-[220px] flex-1">
            <label htmlFor="wf-title" className="sr-only">
              Workflow name
            </label>
            <input
              id="wf-title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              onBlur={commitTitle}
              onKeyDown={(e) => e.key === "Enter" && (e.target as HTMLInputElement).blur()}
              disabled={!!preview}
              className="w-full max-w-[420px] truncate rounded-md bg-transparent px-1 text-xl font-semibold tracking-tight outline-none hover:bg-[#1c1d2a] focus:bg-[#1c1d2a]"
            />
            <div className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1 px-1 text-xs text-[#9393aa]">
              <span>
                {wf.nodes.length} stages · {wf.edges.length} connections
              </span>
              <span aria-live="polite">· {dirty ? "Unsaved changes" : savedSnap ? "Saved" : "Not saved"}</span>
              <span className="pill whitespace-nowrap border-warn/40 text-warn" title="An arbitrary DAG drawn here is a design. It is not necessarily executable, and ModelFlow does not run it.">
                Visual design — not necessarily executable
              </span>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-1.5 sm:gap-2">
            <button type="button" className="btn-ghost text-lg" onClick={doUndo} disabled={!canUndo(hist) || !!preview} aria-label="Undo" title="Undo (⌘/Ctrl+Z)">
              ↶
            </button>
            <button type="button" className="btn-ghost text-lg" onClick={doRedo} disabled={!canRedo(hist) || !!preview} aria-label="Redo" title="Redo (⌘/Ctrl+Shift+Z)">
              ↷
            </button>
            <button type="button" className="btn-primary px-3.5 py-2.5 sm:px-5 sm:py-3" onClick={() => setPlannerOpen((o) => !o)} aria-expanded={plannerOpen} disabled={!!preview}>
              ✦ Generate<span className="hidden md:inline"> workflow</span>
            </button>
            <button type="button" className="btn-secondary" onClick={() => openTab("review")} aria-pressed={tab === "review"}>
              Review
              {audit.counts.error + audit.counts.warning > 0 && (
                <span className="rounded-full bg-warn/20 px-1.5 text-[11px] text-warn" aria-label={`${audit.counts.error + audit.counts.warning} issues`}>
                  {audit.counts.error + audit.counts.warning}
                </span>
              )}
            </button>
            <button type="button" className="btn-secondary" onClick={save} disabled={!!preview}>
              Save<span className="hidden md:inline"> version</span>
            </button>
          </div>
        </div>

        <div ref={canvasRef} className="relative min-h-0 flex-1">
          <ReactFlow<StageFlowNode, Edge>
            nodes={rfNodes}
            edges={rfEdges}
            nodeTypes={nodeTypes}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onDelete={onDelete}
            onConnect={onConnect}
            onReconnect={onReconnect}
            onConnectEnd={(event, state) => {
              if (preview || state.isValid === true) return;
              const pt = "changedTouches" in event ? event.changedTouches[0] : event;
              const el = pt ? document.elementFromPoint(pt.clientX, pt.clientY) : null;
              const target = (el?.closest(".react-flow__node") as HTMLElement | null)?.dataset.id;
              const source = state.fromNode?.id;
              if (!target || !source) return;
              const edges = hist.present.edges;
              // A drag can start from an input handle too; normalise to source -> target.
              const [s, t] = state.fromHandle?.type === "target" ? [target, source] : [source, target];
              if (s === t || wouldCreateCycle(edges, s, t)) showToast("That connection would create a cycle. Workflows must be acyclic.");
              else if (edges.some((e) => e.source === s && e.target === t)) showToast("Those stages are already connected.");
            }}
            isValidConnection={isValidConnection}
            onNodeClick={() => setTab((t) => (t === null || t === "evidence" ? "stage" : t))}
            onNodeDragStart={() => {
              dragging.current = true;
            }}
            onNodeDragStop={(_, __, nodes) => {
              dragging.current = false;
              const moved = new Map(nodes.map((n) => [n.id, n.position]));
              const changed = hist.present.nodes.some((n) => {
                const p = moved.get(n.id);
                return p && (p.x !== n.position.x || p.y !== n.position.y);
              });
              if (changed) commitWf((w) => ({ ...w, nodes: w.nodes.map((n) => (moved.has(n.id) ? { ...n, position: { ...moved.get(n.id)! } } : n)) }));
            }}
            onPaneClick={() => {
              setSelectedId(null);
              setPlannerOpen(false);
            }}
            nodesDraggable={!preview}
            nodesConnectable={!preview}
            elementsSelectable={!preview}
            edgesReconnectable={!preview}
            deleteKeyCode={preview ? null : ["Backspace", "Delete"]}
            colorMode="dark"
            minZoom={0.2}
            maxZoom={2}
            fitView
            proOptions={{ hideAttribution: false }}
            aria-label="Workflow canvas"
          >
            <Background variant={BackgroundVariant.Dots} gap={24} size={1.4} color="#414059" />
            <Controls position="bottom-left" showInteractive={false} />
          </ReactFlow>

          {/* Planner popover (top of canvas) */}
          {plannerOpen && !preview && (
            <section
              aria-label="Generate workflow"
              className="absolute inset-x-3 top-3 z-20 mx-auto max-w-[820px] rounded-[19px] border border-[#5b527a] bg-[#1b1a2aec] p-5 shadow-[0_23px_65px_#0009] backdrop-blur-xl sm:inset-x-6 sm:p-6"
            >
              <div className="mb-3 flex items-start justify-between gap-3">
                <div>
                  <h2 className="text-[22px] font-semibold tracking-tight">What are you building?</h2>
                  <p className="text-[13px] text-[#aaa8bf]">Describe your goal and preview an editable workflow on the canvas.</p>
                </div>
                <button type="button" className="btn-ghost text-lg" aria-label="Close generator" onClick={() => setPlannerOpen(false)}>
                  ×
                </button>
              </div>
              <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
                <label htmlFor="planner-goal" className="sr-only">
                  Goal
                </label>
                <textarea
                  id="planner-goal"
                  autoFocus
                  value={plannerGoal}
                  onChange={(e) => setPlannerGoal(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && (e.metaKey || e.ctrlKey) && generateFromStudio()}
                  placeholder="e.g. Predict customer churn, then evaluate performance and explain the key drivers in parallel."
                  className="min-h-[85px] flex-1 resize-y rounded-xl border border-[#504862] bg-[#131420] p-3.5 text-[15px] leading-normal text-[#f6f2ff] outline-none focus:border-accent"
                />
                <button type="button" className="btn-primary min-h-12" onClick={generateFromStudio} disabled={plannerBusy || !plannerGoal.trim()}>
                  {plannerBusy ? "Generating…" : "Generate preview ↗"}
                </button>
              </div>
              <div className="mb-2 mt-4 flex flex-wrap gap-2">
                {PLANNER_EXAMPLES.map((ex) => (
                  <button key={ex.label} type="button" className="rounded-full border border-[#4d4566] px-3 py-2 text-xs text-[#d4cbed] hover:border-accent" onClick={() => setPlannerGoal(ex.goal)}>
                    {ex.label}
                  </button>
                ))}
              </div>
              <p className="text-xs text-[#aaa8bf]">{MOCK_PLANNER_LABEL}. Uses built-in templates; no Bedrock call, no quality prediction, models left unassigned.</p>
            </section>
          )}

          {/* Single preview location: on the canvas */}
          {preview && (
            <section
              aria-label="Preview of proposed changes"
              className="absolute left-1/2 top-3 z-20 flex w-[min(640px,calc(100%-24px))] -translate-x-1/2 flex-wrap items-center gap-3 rounded-2xl border border-[#8574c0] bg-[#211e33ed] px-4 py-3 shadow-[0_22px_60px_#0008]"
            >
              <div className="min-w-0 flex-1">
                <p className="text-[10px] font-extrabold tracking-[0.12em] text-[#c7b9ff]">{PREVIEW_BROW[preview.kind]}</p>
                <p className="mt-1 text-[13px] text-[#eee9ff]">{summarizeDiff(preview.diff)}</p>
                <p className="mt-0.5 text-[11.5px] text-muted">{preview.detail}</p>
                <p className="mt-0.5 text-[10.5px] text-soft">{preview.label}</p>
                {preview.warnings.length > 0 && (
                  <details className="mt-1 text-[11.5px] text-warn">
                    <summary className="cursor-pointer">{preview.warnings.length} note(s)</summary>
                    <ul className="list-disc pl-4">
                      {preview.warnings.map((w, i) => (
                        <li key={i}>{w}</li>
                      ))}
                    </ul>
                  </details>
                )}
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <button type="button" className="btn-primary px-3.5 py-2.5 text-[13px]" onClick={() => applyPreview(false)}>
                  Apply ✓
                </button>
                <button type="button" className="btn-secondary px-3 py-2 text-[13px]" onClick={() => applyPreview(true)}>
                  Edit
                </button>
                <button type="button" className="btn-text px-1.5 text-[13px]" onClick={() => setPreview(null)}>
                  Discard
                </button>
              </div>
            </section>
          )}

          {wf.nodes.length === 0 && !preview && !plannerOpen && (
            <div className="pointer-events-none absolute inset-0 grid place-items-center p-6">
              <div className="pointer-events-auto max-w-md rounded-2xl border border-line bg-[#161822d9] p-6 text-center">
                <p className="text-lg font-semibold">Start your workflow</p>
                <p className="mt-2 text-sm text-muted">Generate a draft from a goal, add stages from the left, or import a definition.</p>
                <div className="mt-4 flex flex-wrap justify-center gap-2">
                  <button type="button" className="btn-primary" onClick={() => setPlannerOpen(true)}>
                    ✦ Generate workflow
                  </button>
                  <button type="button" className="btn-secondary" onClick={() => addStage("custom", "New stage")}>
                    + Add a stage
                  </button>
                </div>
              </div>
            </div>
          )}

          {!preview && wf.nodes.length > 0 && (
            <p className="pointer-events-none absolute bottom-5 left-16 hidden max-w-[calc(100%-300px)] rounded-[11px] border border-line bg-[#161822d9] px-3.5 py-2.5 text-xs text-[#a0a1b4] xl:block">
              Drag dot → dot to connect · select + Delete to remove · drag an edge end to reconnect · ⌘Z / Ctrl+Z to undo
            </p>
          )}

          {tab !== "ask" && (
            <button
              type="button"
              onClick={() => setTab("ask")}
              className="absolute bottom-5 right-5 z-10 rounded-full bg-[#ac9cff] px-5 py-3.5 text-sm font-bold text-[#16121f] shadow-[0_10px_25px_#0006] hover:bg-[#c3b5ff]"
            >
              ✦ Ask ModelFlow
            </button>
          )}

          {toast && (
            <div role="status" className="absolute bottom-20 left-1/2 z-30 -translate-x-1/2 rounded-[11px] border border-[#7966a0] bg-[#302941] px-4 py-3 text-[13px] text-[#f0eafa] shadow-[0_16px_35px_#0008]">
              {toast}
            </div>
          )}
        </div>
      </main>

      {/* Right panel: docked beside the canvas (overlay only on very narrow screens) */}
      {tab && (
        <aside
          aria-label="Side panel"
          className="absolute inset-y-0 right-0 z-30 flex w-full max-w-[380px] flex-col border-l border-line bg-panel shadow-[-10px_0_30px_#0007] sm:static sm:w-[300px] sm:shadow-none lg:w-[340px]"
        >
          <div className="flex items-center justify-between gap-2 border-b border-line px-3 pt-3">
            <div role="tablist" aria-label="Panel sections" className="flex gap-0.5">
              {(
                [
                  ["stage", "Stage"],
                  ["review", "Review"],
                  ["evidence", "Evidence"],
                  ["ask", "Ask"],
                ] as [PanelTab, string][]
              ).map(([t, label]) => (
                <button
                  key={t}
                  role="tab"
                  id={`tab-${t}`}
                  aria-selected={tab === t}
                  aria-controls={`panel-${t}`}
                  type="button"
                  onClick={() => setTab(t)}
                  className={`rounded-t-md border-b-2 px-2.5 py-2 text-[13px] ${tab === t ? "border-accent text-ink" : "border-transparent text-muted hover:text-ink"}`}
                >
                  {label}
                </button>
              ))}
            </div>
            <button type="button" className="btn-ghost text-lg" aria-label="Close side panel" onClick={() => setTab(null)}>
              ×
            </button>
          </div>
          <div className="min-h-0 flex-1 overflow-y-auto px-5 py-5">
            <div role="tabpanel" id="panel-stage" aria-labelledby="tab-stage" hidden={tab !== "stage"}>
              {preview ? (
                <p className="text-sm text-muted">Apply or discard the preview to edit stages.</p>
              ) : selectedNode ? (
                <NodePanel node={selectedNode} workflow={wf} onChange={(p) => updateNode(selectedNode.id, p)} onDelete={() => deleteNode(selectedNode.id)} />
              ) : (
                <p className="text-sm leading-relaxed text-muted">Select a stage on the canvas to edit its name, task type, model, inputs and outputs.</p>
              )}
            </div>
            <div role="tabpanel" id="panel-review" aria-labelledby="tab-review" hidden={tab !== "review"}>
              <AuditPanel report={audit} onFocusNode={focusNode} />
            </div>
            <div role="tabpanel" id="panel-evidence" aria-labelledby="tab-evidence" hidden={tab !== "evidence"}>
              {tab === "evidence" && <EvidencePanel node={selectedNode} />}
            </div>
            <div role="tabpanel" id="panel-ask" aria-labelledby="tab-ask" hidden={tab !== "ask"} className="h-full">
              <ChatPanel workflow={wf} selectedNodeId={selectedId} previewActive={!!preview} onProposal={onChatProposal} />
            </div>
          </div>
        </aside>
      )}

      <ImportDialog
        open={importOpen}
        onClose={() => setImportOpen(false)}
        fallbackId={wf.id}
        onImport={(w, warnings, sourceName) => {
          setImportOpen(false);
          startPreview("import", hist.present, { ...w, id: hist.present.id }, `Imported from ${sourceName}`, "Replaces the canvas. Check the structure, then apply.", warnings);
        }}
      />
    </div>
  );
}

function PaletteHeading({ children }: { children: React.ReactNode }) {
  return <p className="mb-2 hidden px-2.5 text-[11px] font-bold tracking-[0.14em] text-[#8f90a7] lg:block">{String(children).toUpperCase()}</p>;
}

function Glyph({ children }: { children: React.ReactNode }) {
  return (
    <span aria-hidden className="grid h-[26px] w-[26px] shrink-0 place-items-center rounded-lg border border-[#444257] font-bold text-[#b1a3fc]">
      {children}
    </span>
  );
}

function PaletteButton({ glyph, label, onClick, disabled }: { glyph: string; label: string; onClick: () => void; disabled?: boolean }) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      aria-label={label}
      title={label}
      className="flex w-full items-center gap-2.5 rounded-[10px] px-2 py-2.5 text-left text-sm text-[#cac8d9] hover:bg-[#272636] hover:text-white disabled:opacity-40"
    >
      <Glyph>{glyph}</Glyph>
      <span className="hidden lg:inline">{label}</span>
    </button>
  );
}
