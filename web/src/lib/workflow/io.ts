import { parse as parseYaml, stringify as stringifyYaml } from "yaml";
import { parseWorkflow, type ParseResult, type Workflow } from "./schema";

export type ImportFormat = "json" | "yaml";

export function exportWorkflowJson(w: Workflow): string {
  return JSON.stringify(w, null, 2);
}

export function exportWorkflowYaml(w: Workflow): string {
  return stringifyYaml(JSON.parse(JSON.stringify(w)));
}

export function detectFormat(text: string): ImportFormat {
  const t = text.trimStart();
  return t.startsWith("{") || t.startsWith("[") ? "json" : "yaml";
}

/** Parse JSON or YAML text into a Workflow (shape only; run validateWorkflow for graph checks). */
export function importWorkflowText(text: string, opts: { fallbackId?: string; now?: string } = {}): ParseResult & { format?: ImportFormat } {
  if (!text.trim()) return { ok: false, errors: ["Nothing to import: the text is empty."] };
  const format = detectFormat(text);
  let data: unknown;
  try {
    data = format === "json" ? JSON.parse(text) : parseYaml(text, { maxAliasCount: 50 });
  } catch (err) {
    return { ok: false, errors: [`Could not parse ${format.toUpperCase()}: ${(err as Error).message}`] };
  }
  const res = parseWorkflow(data, opts);
  return { ...res, format };
}
