import { NextResponse } from "next/server";
import { getPlannerProvider } from "@/lib/planner/providers";
import { ProviderNotEnabledError } from "@/lib/planner/types";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const MAX_GOAL_CHARS = 2000;

/**
 * POST /api/plan  { goal: string } -> PlanResponse
 * Uses the deterministic mock planner (no network). Output is a template
 * draft labelled as such; it is never executed.
 */
export async function POST(req: Request) {
  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "Body must be JSON." }, { status: 400 });
  }
  const goal = typeof (body as { goal?: unknown })?.goal === "string" ? (body as { goal: string }).goal.trim() : "";
  if (!goal) return NextResponse.json({ error: "Describe a goal first." }, { status: 400 });
  if (goal.length > MAX_GOAL_CHARS) return NextResponse.json({ error: `Goal is too long (max ${MAX_GOAL_CHARS} characters).` }, { status: 413 });

  try {
    const result = await getPlannerProvider().plan({ goal });
    return NextResponse.json(result);
  } catch (err) {
    if (err instanceof ProviderNotEnabledError) return NextResponse.json({ error: err.message }, { status: 503 });
    return NextResponse.json({ error: "Planner failed." }, { status: 500 });
  }
}
