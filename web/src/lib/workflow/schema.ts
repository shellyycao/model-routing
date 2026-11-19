/**
 * Versioned ModelFlow workflow definition (framework-free).
 *
 * A workflow is a *visual design*: an arbitrary DAG of stages. It is not
 * necessarily executable, and nothing in this module runs anything.
 */

export const SCHEMA_VERSION = 1 as const;
export type SchemaVersion = typeof SCHEMA_VERSION;

export const TASK_TYPES = [
  "source",
  "cleaning",
  "transformation",
  "analysis",
  "modeling",
  "evaluation",
  "explanation",
  "retrieval",
  "extraction",
  "review",
  "reporting",
  "merge",
  "output",
  "custom",
] as const;
export type TaskType = (typeof TASK_TYPES)[number];

export const TASK_TYPE_LABELS: Record<TaskType, string> = {
  source: "Input / source",
  cleaning: "Data cleaning",
  transformation: "Transformation",
  analysis: "Analysis",
  modeling: "Modeling",
  evaluation: "Evaluation",
  explanation: "Explanation",
  retrieval: "Retrieval",
  extraction: "Extraction",
  review: "Review / verification",
  reporting: "Reporting",
  merge: "Merge / combine",
  output: "Output / deliverable",
  custom: "Custom",
};

/** Task types that normally do not call a model (no "unassigned" warning). */
export const NON_MODEL_TASK_TYPES: ReadonlySet<TaskType> = new Set(["source", "output", "merge"]);

/** How a stage with several incoming edges combines its inputs. */
export const MERGE_STRATEGIES = ["unspecified", "wait-all", "first-available", "concatenate", "custom"] as const;
export type MergeStrategy = (typeof MERGE_STRATEGIES)[number];

export interface ExecutionConfig {
  maxOutputTokens?: number;
  temperature?: number;
  timeoutSeconds?: number;
  notes?: string;
}

export interface Position {
  x: number;
  y: number;
}

export interface WorkflowNode {
  id: string;
  name: string;
  description: string;
  taskType: TaskType;
  /** A model option id from `models.ts` ("unassigned", "custom", or a tested model). */
  model: string;
  /** Free-text label when model === "custom" (always unverified). */
  customModelLabel?: string;
  /** Declared input requirements (artifact names). */
  inputs: string[];
  /** Declared outputs (artifact names). */
  outputs: string[];
  mergeStrategy?: MergeStrategy;
  executionConfig?: ExecutionConfig;
  position: Position;
}

export interface WorkflowEdge {
  id: string;
  source: string;
  target: string;
}

export type WorkflowOrigin = "blank" | "example" | "import" | "template-mock" | "ai-draft";

export interface WorkflowMeta {
  createdAt: string;
  updatedAt: string;
  origin: WorkflowOrigin;
}

export interface Workflow {
  schemaVersion: SchemaVersion;
  id: string;
  name: string;
  description: string;
  goal?: string;
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  meta: WorkflowMeta;
}

export function emptyWorkflow(id: string, name = "Untitled workflow", now = new Date().toISOString()): Workflow {
  return {
    schemaVersion: SCHEMA_VERSION,
    id,
    name,
    description: "",
    nodes: [],
    edges: [],
    meta: { createdAt: now, updatedAt: now, origin: "blank" },
  };
}

export function makeNode(partial: Partial<WorkflowNode> & Pick<WorkflowNode, "id">): WorkflowNode {
  return {
    name: "New stage",
    description: "",
    taskType: "custom",
    model: "unassigned",
    inputs: [],
    outputs: [],
    position: { x: 0, y: 0 },
    ...partial,
  };
}

export function edgeIdFor(source: string, target: string): string {
  return `e_${source}__${target}`;
}

// ---------------------------------------------------------------------------
// Structural parsing (shape checks only; graph checks live in validate.ts)
// ---------------------------------------------------------------------------

export type ParseResult = { ok: true; workflow: Workflow; warnings: string[] } | { ok: false; errors: string[] };

const isObj = (v: unknown): v is Record<string, unknown> => typeof v === "object" && v !== null && !Array.isArray(v);
const isStr = (v: unknown): v is string => typeof v === "string";
const strArr = (v: unknown): string[] => (Array.isArray(v) ? v.filter(isStr) : []);

/**
 * Parse an unknown value into a Workflow. Accepts schemaVersion 1.
 * Missing optional fields are filled with defaults and reported as warnings.
 */
export function parseWorkflow(input: unknown, opts: { fallbackId?: string; now?: string } = {}): ParseResult {
  const errors: string[] = [];
  const warnings: string[] = [];
  if (!isObj(input)) return { ok: false, errors: ["Workflow must be a JSON/YAML object."] };

  const version = input.schemaVersion;
  if (version === undefined) {
    warnings.push("schemaVersion missing; assumed 1.");
  } else if (version !== SCHEMA_VERSION) {
    return { ok: false, errors: [`Unsupported schemaVersion ${JSON.stringify(version)} (this app reads version ${SCHEMA_VERSION}).`] };
  }

  if (!Array.isArray(input.nodes)) errors.push("`nodes` must be an array.");
  if (input.edges !== undefined && !Array.isArray(input.edges)) errors.push("`edges` must be an array.");
  if (errors.length) return { ok: false, errors };

  const nodes: WorkflowNode[] = [];
  (input.nodes as unknown[]).forEach((raw, i) => {
    if (!isObj(raw)) {
      errors.push(`nodes[${i}] is not an object.`);
      return;
    }
    if (!isStr(raw.id) || raw.id.trim() === "") {
      errors.push(`nodes[${i}] is missing a string \`id\`.`);
      return;
    }
    const taskType = (TASK_TYPES as readonly string[]).includes(raw.taskType as string) ? (raw.taskType as TaskType) : "custom";
    if (raw.taskType !== undefined && taskType === "custom" && raw.taskType !== "custom") {
      warnings.push(`nodes[${i}] has unknown taskType ${JSON.stringify(raw.taskType)}; set to "custom".`);
    }
    const pos = isObj(raw.position) ? raw.position : {};
    const merge = (MERGE_STRATEGIES as readonly string[]).includes(raw.mergeStrategy as string)
      ? (raw.mergeStrategy as MergeStrategy)
      : undefined;
    const exec = isObj(raw.executionConfig) ? raw.executionConfig : undefined;
    nodes.push({
      id: raw.id,
      name: isStr(raw.name) ? raw.name : isStr(raw.label) ? raw.label : raw.id,
      description: isStr(raw.description) ? raw.description : "",
      taskType,
      model: isStr(raw.model) && raw.model ? raw.model : "unassigned",
      customModelLabel: isStr(raw.customModelLabel) ? raw.customModelLabel : undefined,
      inputs: strArr(raw.inputs),
      outputs: strArr(raw.outputs),
      mergeStrategy: merge,
      executionConfig: exec
        ? {
            maxOutputTokens: typeof exec.maxOutputTokens === "number" ? exec.maxOutputTokens : undefined,
            temperature: typeof exec.temperature === "number" ? exec.temperature : undefined,
            timeoutSeconds: typeof exec.timeoutSeconds === "number" ? exec.timeoutSeconds : undefined,
            notes: isStr(exec.notes) ? exec.notes : undefined,
          }
        : undefined,
      position: {
        x: typeof pos.x === "number" ? pos.x : typeof raw.x === "number" ? raw.x : i * 260,
        y: typeof pos.y === "number" ? pos.y : typeof raw.y === "number" ? raw.y : 120,
      },
    });
  });

  const edges: WorkflowEdge[] = [];
  ((input.edges as unknown[] | undefined) ?? []).forEach((raw, i) => {
    if (!isObj(raw)) {
      errors.push(`edges[${i}] is not an object.`);
      return;
    }
    // Accept {source,target} or the prototype's {from,to}.
    const source = isStr(raw.source) ? raw.source : isStr(raw.from) ? raw.from : undefined;
    const target = isStr(raw.target) ? raw.target : isStr(raw.to) ? raw.to : undefined;
    if (!source || !target) {
      errors.push(`edges[${i}] needs string \`source\` and \`target\`.`);
      return;
    }
    edges.push({ id: isStr(raw.id) && raw.id ? raw.id : edgeIdFor(source, target), source, target });
  });

  if (errors.length) return { ok: false, errors };

  const now = opts.now ?? new Date().toISOString();
  const meta = isObj(input.meta) ? input.meta : {};
  const origins: WorkflowOrigin[] = ["blank", "example", "import", "template-mock", "ai-draft"];
  return {
    ok: true,
    warnings,
    workflow: {
      schemaVersion: SCHEMA_VERSION,
      id: isStr(input.id) && input.id ? input.id : opts.fallbackId ?? "imported",
      name: isStr(input.name) && input.name.trim() ? input.name : "Imported workflow",
      description: isStr(input.description) ? input.description : "",
      goal: isStr(input.goal) ? input.goal : undefined,
      nodes,
      edges,
      meta: {
        createdAt: isStr(meta.createdAt) ? meta.createdAt : now,
        updatedAt: isStr(meta.updatedAt) ? meta.updatedAt : now,
        origin: origins.includes(meta.origin as WorkflowOrigin) ? (meta.origin as WorkflowOrigin) : "import",
      },
    },
  };
}
