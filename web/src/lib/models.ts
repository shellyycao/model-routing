/**
 * Model options for the stage "assigned model" dropdown.
 *
 * Only models that appear in this project's saved experiments are listed,
 * plus "Unassigned" and "Custom (unverified)". `testedIn` says *where* each
 * model was tested; it is not a claim that the model suits any given stage.
 *
 * Bedrock ids are copied from configs/models.yaml and
 * results/processed/independent_v2/price_matched_v2_analysis.json for reference only;
 * the website never invokes them.
 */

export interface ModelOption {
  id: string;
  label: string;
  /** Alias in the three-stage workflow experiment (configs/models.yaml), if any. */
  workflowAlias?: "A" | "B" | "C";
  /** Alias in price-matched-v2 analysis, if any. */
  priceMatchedAlias?: "sonnet_4_6" | "kimi_k3" | "glm_5";
  testedIn: string[];
  tested: boolean;
}

export const UNASSIGNED = "unassigned";
export const CUSTOM = "custom";

export const MODEL_OPTIONS: ModelOption[] = [
  { id: UNASSIGNED, label: "Unassigned", testedIn: [], tested: false },
  {
    id: "sonnet_4_6",
    label: "Claude Sonnet 4.6",
    workflowAlias: "A",
    priceMatchedAlias: "sonnet_4_6",
    testedIn: ["Three-stage workflow experiment (alias A)", "Price-matched-v2 task benchmark (A1–A3)"],
    tested: true,
  },
  {
    id: "nova_pro",
    label: "Amazon Nova Pro",
    workflowAlias: "B",
    testedIn: ["Three-stage workflow experiment (alias B)"],
    tested: true,
  },
  {
    id: "gpt_oss_120b",
    label: "gpt-oss-120b",
    workflowAlias: "C",
    testedIn: ["Three-stage workflow experiment (alias C)"],
    tested: true,
  },
  {
    id: "kimi_k3",
    label: "Kimi K3",
    priceMatchedAlias: "kimi_k3",
    testedIn: ["Price-matched-v2 task benchmark (A1–A3)"],
    tested: true,
  },
  {
    id: "glm_5",
    label: "GLM 5",
    priceMatchedAlias: "glm_5",
    testedIn: ["Price-matched-v2 task benchmark (A1–A3)"],
    tested: true,
  },
  { id: CUSTOM, label: "Custom (unverified)", testedIn: [], tested: false },
];

export function modelOption(id: string): ModelOption | undefined {
  return MODEL_OPTIONS.find((m) => m.id === id);
}

export function modelLabel(id: string, customLabel?: string): string {
  if (id === CUSTOM) return customLabel?.trim() ? `${customLabel.trim()} (custom, unverified)` : "Custom (unverified)";
  return modelOption(id)?.label ?? `${id} (unknown, unverified)`;
}

export function isKnownModel(id: string): boolean {
  return MODEL_OPTIONS.some((m) => m.id === id);
}
