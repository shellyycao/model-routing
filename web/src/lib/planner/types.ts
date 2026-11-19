/**
 * Planner and chat provider contracts.
 *
 * Providers return *proposals* only. The UI shows a diff on the canvas and
 * the user decides (Apply / Edit / Discard). Providers never execute code and
 * never mutate the user's graph.
 */
import type { GraphEditAction, WorkflowDiff } from "../workflow/edits";
import type { Workflow } from "../workflow/schema";
import type { ValidationReport } from "../workflow/validate";

export type ProviderKind = "mock" | "bedrock";

export interface Provenance {
  provider: ProviderKind;
  /** Human-readable label that MUST be shown next to any output. */
  label: string;
  /** True only for real model output. The mock provider always sets false. */
  aiGenerated: boolean;
  generatedAt: string;
  modelId?: string;
}

export const MOCK_PLANNER_LABEL = "Template draft (mock planner) — not AI-generated yet";
export const MOCK_CHAT_LABEL = "Rule-based reply (mock assistant) — not AI-generated yet";

// --- Planner ---------------------------------------------------------------

export interface PlanRequest {
  goal: string;
}

export interface PlanResponse {
  draft: Workflow;
  validation: ValidationReport;
  provenance: Provenance;
  /** Short explanation of how the draft was produced (template choice, not reasoning). */
  rationale: string;
}

export interface PlannerProvider {
  readonly kind: ProviderKind;
  plan(req: PlanRequest): Promise<PlanResponse>;
}

// --- Chat ------------------------------------------------------------------

export interface ChatContext {
  page: "home" | "studio" | "library";
  workflow: Workflow;
  selectedNodeId?: string | null;
}

export interface ChatRequest {
  message: string;
  context: ChatContext;
}

export interface EditProposal {
  summary: string;
  actions: GraphEditAction[];
  diff: WorkflowDiff;
  validation: ValidationReport;
  /** The workflow after applying `actions` (for canvas preview). */
  preview: Workflow;
}

export interface ChatResponse {
  reply: string;
  proposal?: EditProposal;
  provenance: Provenance;
}

export interface ChatProvider {
  readonly kind: ProviderKind;
  respond(req: ChatRequest): Promise<ChatResponse>;
}

export class ProviderNotEnabledError extends Error {
  constructor(message = "Bedrock provider not enabled — requires user-approved budget") {
    super(message);
    this.name = "ProviderNotEnabledError";
  }
}
