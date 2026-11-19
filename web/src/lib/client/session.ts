"use client";
/**
 * Browser-only helpers: id generation, Home → Studio hand-off and API calls.
 */
import type { ChatContext, ChatResponse, PlanResponse } from "../planner/types";
import type { Workflow } from "../workflow/schema";

export function newId(prefix: string): string {
  const rnd = typeof crypto !== "undefined" && "randomUUID" in crypto ? crypto.randomUUID().slice(0, 8) : Math.random().toString(36).slice(2, 10);
  return `${prefix}_${Date.now().toString(36)}${rnd}`;
}

/** A draft waiting to be previewed on the Studio canvas. */
export type PendingDraft =
  | { kind: "planner"; response: PlanResponse }
  | { kind: "import"; workflow: Workflow; warnings: string[]; sourceName: string };

const PENDING_KEY = "modelflow.pending-draft";

export function setPendingDraft(d: PendingDraft) {
  try {
    sessionStorage.setItem(PENDING_KEY, JSON.stringify(d));
  } catch {
    /* ignore quota / privacy mode */
  }
}

export function takePendingDraft(): PendingDraft | null {
  try {
    const raw = sessionStorage.getItem(PENDING_KEY);
    sessionStorage.removeItem(PENDING_KEY);
    return raw ? (JSON.parse(raw) as PendingDraft) : null;
  } catch {
    return null;
  }
}

async function postJson<T>(url: string, body: unknown): Promise<T> {
  const res = await fetch(url, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body) });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error((data as { error?: string }).error ?? `Request failed (${res.status})`);
  return data as T;
}

export const requestPlan = (goal: string) => postJson<PlanResponse>("/api/plan", { goal });
export const requestChat = (message: string, context: ChatContext) => postJson<ChatResponse>("/api/chat", { message, context });

export function downloadText(filename: string, text: string, type = "application/json") {
  const url = URL.createObjectURL(new Blob([text], { type }));
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export function slugify(s: string): string {
  return s.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "workflow";
}
