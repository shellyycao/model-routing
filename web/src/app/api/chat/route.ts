import { NextResponse } from "next/server";
import { getChatProvider } from "@/lib/planner/providers";
import { ProviderNotEnabledError, type ChatContext } from "@/lib/planner/types";
import { parseWorkflow } from "@/lib/workflow/schema";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const MAX_MESSAGE_CHARS = 2000;
const MAX_NODES = 300;
const PAGES: ChatContext["page"][] = ["home", "studio", "library"];

/**
 * POST /api/chat  { message, context: { page, workflow, selectedNodeId } } -> ChatResponse
 * Uses the deterministic mock assistant (no network). Edits come back as a
 * proposal (typed actions + diff); the client validates and previews them and
 * the user must click Apply.
 */
export async function POST(req: Request) {
  let body: Record<string, unknown>;
  try {
    body = (await req.json()) as Record<string, unknown>;
  } catch {
    return NextResponse.json({ error: "Body must be JSON." }, { status: 400 });
  }
  const message = typeof body.message === "string" ? body.message.trim() : "";
  if (!message) return NextResponse.json({ error: "Message is empty." }, { status: 400 });
  if (message.length > MAX_MESSAGE_CHARS) return NextResponse.json({ error: `Message is too long (max ${MAX_MESSAGE_CHARS}).` }, { status: 413 });

  const ctx = (body.context ?? {}) as Record<string, unknown>;
  const parsed = parseWorkflow(ctx.workflow ?? { nodes: [], edges: [] });
  if (!parsed.ok) return NextResponse.json({ error: `Workflow context is invalid: ${parsed.errors.join(" ")}` }, { status: 400 });
  if (parsed.workflow.nodes.length > MAX_NODES) return NextResponse.json({ error: `Workflow too large (max ${MAX_NODES} stages).` }, { status: 413 });

  const context: ChatContext = {
    page: PAGES.includes(ctx.page as ChatContext["page"]) ? (ctx.page as ChatContext["page"]) : "studio",
    workflow: parsed.workflow,
    selectedNodeId: typeof ctx.selectedNodeId === "string" ? ctx.selectedNodeId : null,
  };

  try {
    return NextResponse.json(await getChatProvider().respond({ message, context }));
  } catch (err) {
    if (err instanceof ProviderNotEnabledError) return NextResponse.json({ error: err.message }, { status: 503 });
    return NextResponse.json({ error: "Assistant failed." }, { status: 500 });
  }
}
