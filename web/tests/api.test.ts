import { describe, expect, it } from "vitest";
import { POST as chat } from "../src/app/api/chat/route";
import { POST as plan } from "../src/app/api/plan/route";
import { MOCK_PLANNER_LABEL } from "../src/lib/planner/types";
import { wf } from "./helpers";

const req = (body: unknown) => new Request("http://test/api", { method: "POST", headers: { "content-type": "application/json" }, body: typeof body === "string" ? body : JSON.stringify(body) });

describe("/api/plan", () => {
  it("returns a labelled mock draft", async () => {
    const res = await plan(req({ goal: "predict churn" }));
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.provenance).toMatchObject({ provider: "mock", aiGenerated: false, label: MOCK_PLANNER_LABEL });
    expect(data.validation.valid).toBe(true);
  });

  it("rejects bad input", async () => {
    expect((await plan(req("not json"))).status).toBe(400);
    expect((await plan(req({ goal: "  " }))).status).toBe(400);
    expect((await plan(req({ goal: "x".repeat(2001) }))).status).toBe(413);
  });
});

describe("/api/chat", () => {
  it("returns a proposal without mutating the posted workflow", async () => {
    const workflow = wf(["a", "b"], [["a", "b"]]);
    const res = await chat(req({ message: "add checker after B", context: { page: "studio", workflow } }));
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.proposal.diff.addedNodes).toEqual(["n_checker"]);
    expect(data.provenance.aiGenerated).toBe(false);
  });

  it("rejects malformed workflow context and empty messages", async () => {
    expect((await chat(req({ message: "hi", context: { workflow: { nodes: "nope" } } }))).status).toBe(400);
    expect((await chat(req({ message: "", context: {} }))).status).toBe(400);
  });
});
