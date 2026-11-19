import { describe, expect, it } from "vitest";
import { auditWorkflow } from "../src/lib/auditor/audit";
import { BedrockChatProvider, BedrockPlannerProvider } from "../src/lib/planner/bedrockProvider";
import { MockChatProvider, findNode, interpret } from "../src/lib/planner/mockChat";
import { MockPlannerProvider, buildDraft } from "../src/lib/planner/mockPlanner";
import { getChatProvider, getPlannerProvider } from "../src/lib/planner/providers";
import { MOCK_PLANNER_LABEL, ProviderNotEnabledError } from "../src/lib/planner/types";
import { NOW, wf } from "./helpers";

const clock = () => NOW;

describe("MockPlannerProvider", () => {
  it("returns a valid, labelled, non-AI template draft with no models assigned", async () => {
    const r = await new MockPlannerProvider(clock).plan({ goal: "Predict customer churn and check fairness" });
    expect(r.provenance).toMatchObject({ provider: "mock", aiGenerated: false, label: MOCK_PLANNER_LABEL });
    expect(r.validation.valid).toBe(true);
    expect(r.draft.meta.origin).toBe("template-mock");
    expect(r.draft.nodes.every((n) => n.model === "unassigned")).toBe(true);
    expect(r.draft.nodes.some((n) => n.name === "Fairness check")).toBe(true);
    // fan-out + fan-in present
    expect(r.draft.edges.filter((e) => e.source === "n_train").length).toBeGreaterThan(1);
  });

  it("is deterministic and always yields a connected DAG", async () => {
    for (const goal of ["review research papers", "clean and visualize data in parallel", "something else entirely"]) {
      const a = buildDraft(goal, NOW).draft;
      expect(a).toEqual(buildDraft(goal, NOW).draft);
      const audit = auditWorkflow(a);
      expect(audit.counts.error).toBe(0);
      expect(audit.structural.some((f) => f.code === "disconnected" || f.code === "fan-in-merge-unspecified")).toBe(false);
    }
  });

  it("rejects an empty goal", async () => {
    await expect(new MockPlannerProvider(clock).plan({ goal: "  " })).rejects.toThrow();
  });
});

describe("MockChatProvider", () => {
  const base = buildDraft("predict churn", NOW).draft;

  it("proposes (does not apply) an add-after edit with a diff", async () => {
    const r = await new MockChatProvider(clock).respond({ message: "Add a fairness evaluation after model training", context: { page: "studio", workflow: base } });
    expect(r.provenance.aiGenerated).toBe(false);
    expect(r.proposal?.diff.addedNodes).toEqual(["n_fairness_evaluation"]);
    expect(r.proposal?.validation.valid).toBe(true);
    expect(base.nodes.some((n) => n.id === "n_fairness_evaluation")).toBe(false);
  });

  it("inserts before a stage by rewiring its inputs", () => {
    const r = interpret("add outlier removal before train model", base);
    const added = r.proposal!.diff;
    expect(added.removedEdges).toEqual([{ source: "n_features", target: "n_train" }]);
    expect(added.addedEdges).toEqual(expect.arrayContaining([{ source: "n_outlier_removal", target: "n_train" }]));
  });

  it("adds a parallel branch sharing parents and children", () => {
    const r = interpret("add a parallel branch to evaluate model", base);
    const d = r.proposal!.diff;
    expect(d.addedEdges).toEqual(expect.arrayContaining([{ source: "n_train", target: "n_parallel_branch" }, { source: "n_parallel_branch", target: "n_report" }]));
  });

  it("renames, removes and connects; refuses cycles", () => {
    expect(interpret("rename clean data to Prepare data", base).proposal?.diff.modifiedNodes).toEqual([{ id: "n_clean", fields: ["name"] }]);
    expect(interpret("remove explain drivers", base).proposal?.diff.removedNodes).toEqual(["n_explain"]);
    const cyc = interpret("connect write report to load data", base);
    expect(cyc.proposal).toBeUndefined();
    expect(cyc.reply).toMatch(/couldn't/);
  });

  it("answers review requests and other text without proposals or invented numbers", () => {
    expect(interpret("review my workflow", base).reply).toMatch(/Structural review/);
    const other = interpret("why this model?", base);
    expect(other.proposal).toBeUndefined();
    expect(other.reply).not.toMatch(/\d+(\.\d+)?%/);
  });

  it("finds nodes by fuzzy token overlap", () => {
    expect(findNode(base, "model training")?.id).toBe("n_train");
    expect(findNode(base, "zzz")).toBeNull();
  });
});

describe("Bedrock stub", () => {
  it("throws not-enabled and is only selected explicitly", async () => {
    await expect(new BedrockPlannerProvider().plan({ goal: "x" })).rejects.toBeInstanceOf(ProviderNotEnabledError);
    await expect(new BedrockChatProvider().respond({ message: "x", context: { page: "studio", workflow: wf([], []) } })).rejects.toThrow(/requires user-approved budget/);
    expect(getPlannerProvider({}).kind).toBe("mock");
    expect(getChatProvider({}).kind).toBe("mock");
    expect(getPlannerProvider({ MODELFLOW_PROVIDER: "bedrock" }).kind).toBe("bedrock");
  });
});

describe("auditWorkflow", () => {
  it("flags structure, models, fan-in and I/O issues deterministically", () => {
    const w = wf(["a", "b", "c", "d", "x"], [["a", "b"], ["a", "c"], ["b", "d"], ["c", "d"]]);
    w.nodes[0].taskType = "source";
    w.nodes[0].outputs = ["raw"];
    w.nodes[1].inputs = ["raw"];
    w.nodes[1].outputs = ["clean"];
    w.nodes[2].inputs = ["missing thing"];
    w.nodes[3].model = "custom";
    const codes = auditWorkflow(w).structural.map((f) => f.code);
    expect(codes).toEqual(expect.arrayContaining(["disconnected", "unassigned-model", "custom-model-unverified", "fan-in-merge-unspecified", "io-unsatisfied-input", "multiple-entries"]));
    expect(codes).not.toContain("cycle");
  });

  it("flags cycles and missing entry/terminal", () => {
    const codes = auditWorkflow(wf(["a", "b"], [["a", "b"], ["b", "a"]])).structural.map((f) => f.code);
    expect(codes).toEqual(expect.arrayContaining(["no-entry", "no-terminal", "cycle"]));
  });

  it("keeps evidence recommendations empty and every finding deterministic", () => {
    const r = auditWorkflow(wf(["a"], []));
    expect(r.evidence).toEqual([]);
    expect(r.evidenceNotice).toMatch(/Unverified/);
    expect(r.structural.every((f) => f.basis === "deterministic")).toBe(true);
  });
});
