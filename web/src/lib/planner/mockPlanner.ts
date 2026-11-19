/**
 * Deterministic MOCK planner. No network, no model calls.
 *
 * Picks a hand-written template by keyword and returns it as a draft. Output is
 * labelled "Template draft (mock planner) — not AI-generated yet". Models are
 * never pre-assigned: every stage starts "Unassigned".
 */
import { layoutLayered } from "../workflow/layout";
import { SCHEMA_VERSION, edgeIdFor, makeNode, type MergeStrategy, type TaskType, type Workflow } from "../workflow/schema";
import { validateWorkflow } from "../workflow/validate";
import { MOCK_PLANNER_LABEL, type PlanRequest, type PlanResponse, type PlannerProvider } from "./types";

interface StageSpec {
  key: string;
  name: string;
  taskType: TaskType;
  description: string;
  inputs?: string[];
  outputs?: string[];
  after?: string[];
  merge?: MergeStrategy;
}

interface Template {
  id: string;
  title: string;
  match: (g: string) => boolean;
  build: (g: string) => StageSpec[];
}

const has = (g: string, ...words: string[]) => words.some((w) => g.includes(w));

export const TEMPLATES: Template[] = [
  {
    id: "predictive-modeling",
    title: "Predictive modeling",
    match: (g) => has(g, "predict", "churn", "classif", "forecast", "regression", "train a model", "machine learning"),
    build: (g) => {
      const stages: StageSpec[] = [
        { key: "load", name: "Load data", taskType: "source", description: "Read the source dataset.", outputs: ["raw data"] },
        { key: "clean", name: "Clean data", taskType: "cleaning", description: "Fix types, missing values and duplicates.", inputs: ["raw data"], outputs: ["clean data"], after: ["load"] },
        { key: "features", name: "Feature engineering", taskType: "transformation", description: "Derive model features.", inputs: ["clean data"], outputs: ["features"], after: ["clean"] },
        { key: "train", name: "Train model", taskType: "modeling", description: "Fit a predictive model.", inputs: ["features"], outputs: ["trained model"], after: ["features"] },
        { key: "evaluate", name: "Evaluate model", taskType: "evaluation", description: "Measure held-out performance.", inputs: ["trained model"], outputs: ["metrics"], after: ["train"] },
        { key: "explain", name: "Explain drivers", taskType: "explanation", description: "Identify the most important features.", inputs: ["trained model"], outputs: ["feature importance"], after: ["train"] },
      ];
      const reportInputs = ["metrics", "feature importance"];
      const reportAfter = ["evaluate", "explain"];
      if (has(g, "fair", "bias")) {
        stages.push({ key: "fairness", name: "Fairness check", taskType: "evaluation", description: "Compare performance across groups.", inputs: ["trained model"], outputs: ["fairness report"], after: ["train"] });
        reportInputs.push("fairness report");
        reportAfter.push("fairness");
      }
      stages.push({ key: "report", name: "Write report", taskType: "reporting", description: "Summarize results for stakeholders.", inputs: reportInputs, outputs: ["report"], after: reportAfter, merge: "wait-all" });
      return stages;
    },
  },
  {
    id: "literature-review",
    title: "Literature review",
    match: (g) => has(g, "paper", "literature", "citation", "research"),
    build: () => [
      { key: "collect", name: "Collect papers", taskType: "retrieval", description: "Gather candidate papers.", outputs: ["papers"] },
      { key: "screen", name: "Screen relevance", taskType: "review", description: "Keep papers that match the question.", inputs: ["papers"], outputs: ["shortlist"], after: ["collect"] },
      { key: "extract", name: "Extract evidence", taskType: "extraction", description: "Pull claims, methods and results.", inputs: ["shortlist"], outputs: ["evidence table"], after: ["screen"] },
      { key: "cite", name: "Verify citations", taskType: "review", description: "Check that every claim cites a real source.", inputs: ["evidence table"], outputs: ["citation check"], after: ["extract"] },
      { key: "synth", name: "Synthesize findings", taskType: "analysis", description: "Group and compare findings.", inputs: ["evidence table"], outputs: ["synthesis"], after: ["extract"] },
      { key: "write", name: "Write review", taskType: "reporting", description: "Draft the literature review.", inputs: ["synthesis", "citation check"], outputs: ["review"], after: ["cite", "synth"], merge: "wait-all" },
    ],
  },
  {
    id: "parallel-analytics",
    title: "Parallel analytics",
    match: (g) => has(g, "clean", "visual", "explor", "analy", "dashboard", "trend"),
    build: () => [
      { key: "load", name: "Load data", taskType: "source", description: "Read the source dataset.", outputs: ["raw data"] },
      { key: "clean", name: "Clean data", taskType: "cleaning", description: "Fix types, missing values and duplicates.", inputs: ["raw data"], outputs: ["clean data"], after: ["load"] },
      { key: "eda", name: "Exploratory analysis", taskType: "analysis", description: "Compute summary statistics and trends.", inputs: ["clean data"], outputs: ["analysis results"], after: ["clean"] },
      { key: "viz", name: "Create visualizations", taskType: "analysis", description: "Produce charts.", inputs: ["clean data"], outputs: ["charts"], after: ["clean"] },
      { key: "summary", name: "Summarize results", taskType: "reporting", description: "Combine analysis and charts into a summary.", inputs: ["analysis results", "charts"], outputs: ["summary"], after: ["eda", "viz"], merge: "wait-all" },
    ],
  },
];

const GENERIC: Template = {
  id: "generic",
  title: "Generic pipeline",
  match: () => true,
  build: () => [
    { key: "input", name: "Gather inputs", taskType: "source", description: "Collect what the workflow needs.", outputs: ["inputs"] },
    { key: "process", name: "Process", taskType: "custom", description: "Main work step. Rename and describe it.", inputs: ["inputs"], outputs: ["draft result"], after: ["input"] },
    { key: "review", name: "Review", taskType: "review", description: "Check the result.", inputs: ["draft result"], outputs: ["checked result"], after: ["process"] },
    { key: "deliver", name: "Deliver", taskType: "output", description: "Final deliverable.", inputs: ["checked result"], after: ["review"] },
  ],
};

/** Stable short hash for deterministic ids (FNV-1a). */
export function shortHash(s: string): string {
  let h = 0x811c9dc5;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 0x01000193);
  }
  return (h >>> 0).toString(36);
}

export function selectTemplate(goal: string): Template {
  const g = goal.toLowerCase();
  return TEMPLATES.find((t) => t.match(g)) ?? GENERIC;
}

export function buildDraft(goal: string, now: string): { draft: Workflow; template: Template } {
  const template = selectTemplate(goal);
  const specs = template.build(goal.toLowerCase());
  const nodes = specs.map((s) =>
    makeNode({
      id: `n_${s.key}`,
      name: s.name,
      description: s.description,
      taskType: s.taskType,
      model: "unassigned",
      inputs: s.inputs ?? [],
      outputs: s.outputs ?? [],
      mergeStrategy: s.merge,
    }),
  );
  const edges = specs.flatMap((s) => (s.after ?? []).map((p) => ({ id: edgeIdFor(`n_${p}`, `n_${s.key}`), source: `n_${p}`, target: `n_${s.key}` })));
  const trimmed = goal.trim();
  const draft: Workflow = {
    schemaVersion: SCHEMA_VERSION,
    id: `draft_${shortHash(trimmed)}`,
    name: template.id === "generic" ? "Draft workflow" : `${template.title} draft`,
    description: `Template draft for: ${trimmed.slice(0, 200)}`,
    goal: trimmed,
    nodes: layoutLayered(nodes, edges),
    edges,
    meta: { createdAt: now, updatedAt: now, origin: "template-mock" },
  };
  return { draft, template };
}

export class MockPlannerProvider implements PlannerProvider {
  readonly kind = "mock" as const;
  constructor(private clock: () => string = () => new Date().toISOString()) {}

  async plan(req: PlanRequest): Promise<PlanResponse> {
    const goal = (req.goal ?? "").trim();
    if (!goal) throw new Error("Describe a goal first.");
    const now = this.clock();
    const { draft, template } = buildDraft(goal, now);
    return {
      draft,
      validation: validateWorkflow(draft),
      provenance: { provider: "mock", label: MOCK_PLANNER_LABEL, aiGenerated: false, generatedAt: now },
      rationale: `Matched the "${template.title}" template by keywords in your goal. No model was called; models are left unassigned for you to choose.`,
    };
  }
}
