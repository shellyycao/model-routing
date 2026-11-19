# M7 — ModelFlow Website & AI Workflow Copilot (handoff from the user, via ChatGPT, 2026-11-19)

## Product vision
- **Product:** ModelFlow, an explainable AI workflow planning and optimization platform.
- **Headline:** "Your workflow. Smarter decisions."
- **Subtitle:** "Design new workflows or improve existing ones with evidence-backed AI recommendations."
- **Two user journeys,** both leading to the same Visual Workflow Studio:
  1. **Create a Workflow:** the user describes a goal and gets a structured, editable workflow.
  2. **Improve My Workflow:** the user imports or opens a workflow, inspects it, finds weaknesses and
     explores improvements.
- **Visual and interaction reference:** `modelflow_canvas_first_copilot.html`, copied to
  `docs/design/modelflow_canvas_first_copilot.html`. Keep its dark-purple look, open canvas, minimal
  cards and prominent Generate Workflow action. It is not an analytics dashboard.

## 1. Preserve existing research
- **Reuse:**
  - the Bedrock client and cost controls;
  - the model registry;
  - benchmark datasets and result records;
  - the orchestrator;
  - the Router and Decision Traces;
  - counterfactual predictions and validations;
  - evidence provenance.
- **Never modify:** frozen experiments, validators or historical results.

## 2. Architecture
- **Stack:**
  - Next.js + TypeScript;
  - Tailwind;
  - React Flow / XYFlow;
  - AWS Bedrock for the planner and chat;
  - a Vercel-compatible build;
  - versioned JSON workflow definitions.
- **Keep these as separate concerns:**
  - UI;
  - graph state and validation;
  - AI Planner;
  - conversational editing;
  - evidence retrieval;
  - Router integration;
  - persistence.

## 3. Home: two entry points
- **Create a Workflow:**
  - a large natural-language input;
  - a prominent Generate Workflow button;
  - example prompts;
  - a direct transition to the Studio with the draft.
- **Improve My Workflow:**
  - open a saved workflow;
  - import JSON or YAML, or describe a workflow in plain English;
  - review it before applying.
- **Style:** spacious, with no dense dashboards, small buttons or big solid panels.

## 4. Visual Workflow Studio (core)
An editor inspired by AWS Glue Studio.
- **Canvas features:**
  - add, rename, delete and drag nodes;
  - connect nodes with handles;
  - fan-out, fan-in, parallel branches, and branch/merge;
  - prevent cycles;
  - delete and reconnect edges;
  - zoom, pan and fit;
  - undo and redo;
  - save and reopen;
  - import and export.
- **Each node has:**
  - name and description;
  - task type;
  - assigned model;
  - input and output requirements;
  - dependencies;
  - optional execution config.
- **No fixed pipeline.** Users are not constrained to Cleaning → Analysis → Reporting.
- **Executable is not the same as visual.** Clearly label that an arbitrary DAG is a visual design and
  not necessarily executable.

## 5. AI Planner (real Bedrock, M7.2)
- **Flow:** prompt → Bedrock → structured workflow JSON → schema validation → DAG validation → canvas
  preview, with Apply, Edit and Discard.
- **Rules:**
  - Use the existing Bedrock adapter and registry, with a verified, cost-conscious model.
  - Use structured output or tool use.
  - Check IDs, edges, duplicates, disconnected stages and cycles.
  - Never execute generated code.
  - Retry a bounded number of times.
  - Label output as an AI-generated draft.

## 6. Chatbot "Ask ModelFlow" (real Bedrock, M7.3)
- **Context awareness:** it knows the page, the graph, the selected node, the assigned models,
  dependencies, the user's goal, and the evidence available.
- **Capabilities:**
  - A. Create workflows.
  - B. Edit, by returning a structured graph-edit proposal.
  - C. Explain, citing evidence when it exists.
  - D. Suggest improvements, separating verified evidence from estimates.
- **Safety:**
  - It never mutates the graph without confirmation.
  - It edits through typed tools or actions.
  - It shows a diff of added, removed and modified items, and validates before preview.
  - Apply, Reject and Undo all work.
  - It never invents benchmark results or citations.
  - It never claims an unexecuted workflow was tested.
- **Endpoint:** server-side `/api/chat` with credentials kept on the server, streaming if feasible.

## 7. Auditor and recommendations (M7.4)
- **Review Workflow action.** It checks:
  - missing or disconnected dependencies;
  - invalid structure;
  - incompatible input/output contracts;
  - unassigned models;
  - redundant stages;
  - unverified model recommendations.
- **Keep two kinds of findings separate:** deterministic structural problems, and evidence-based
  performance suggestions.
- **Every recommendation shows:**
  - what should change;
  - why;
  - the evidence;
  - the expected benefit;
  - uncertainty;
  - its evidence status: Directly tested, Partially supported or Unverified.
- **Each recommendation can be previewed and accepted or rejected on its own.**

## 8. XAI
- **"Why this model?"** Show task benchmark evidence and the criteria that matter.
- **"Why this workflow?"** Separate LLM planning rationale from validated findings.
- **"What if?"**
  - for tested paths, show the actual observations;
  - for untested paths, label the result a prediction or unverified.
- **Evidence:** link every number to its record, version and trace.
- **Status labels:** Directly tested, Partially supported, Unverified.
- **Never** extrapolate the three-stage workflow results to arbitrary DAGs.
- **Always separate** observed results, predicted results and post-hoc analyses.

## 9. Cost-aware features
- **Show:**
  - estimated cost per stage and per workflow;
  - observed cost;
  - quality–cost comparisons;
  - a Pareto frontier where the evidence supports one;
  - cost counterfactuals.
- **Rules:**
  - Unknown behaviour gets no falsely precise estimate.
  - Label pricing assumptions: region, model version, and anything missing.
  - Missing price is never zero.

## 10. Workflow Library
- **Features:** save, reopen, duplicate, rename, organize, version history, restore, and JSON
  import/export.
- **Storage:** local persistence is acceptable for the MVP. Design the data layer so cloud storage can be
  added later.
- **Credentials:** never stored in the browser.

## 11. UI/UX
- **Look:** dark background, soft purple, large type, open canvas, minimal cards, large primary actions,
  and a clear selected state.
- **Layout:** the canvas comes first. Side panels for node config, chat, explanations and evidence are
  collapsible. The chat must not shrink the canvas to a strip.
- **Quality:** responsive and accessible.

## 12. Research boundaries
- No universal routing-accuracy claims.
- Never silently replace the research Router with an LLM.
- Task evidence is not end-to-end proof.
- Not every DAG is executable.
- LLM rationale is not validated explanation.
- The accuracy of the Planner and Auditor is not yet established.

## 13. Order
- **M7.1** frontend foundation: Next.js app, Home, Studio, DAG editor, state, local persistence.
- **M7.2** real planner.
- **M7.3** chat copilot.
- **M7.4** auditor and XAI.
- **M7.5** QA, tests, Vercel preparation and documented limitations.

## 14. Approval and cost controls
- **No approval needed for:** UI, graph editing, offline tests, read-only research integration.
- **Before any paid Bedrock call, propose:**
  - the model;
  - its pricing;
  - per-request token limits;
  - invocation caps;
  - the total dev/test budget.
- **Never do:**
  - unapproved third-party charges;
  - public deployment;
  - IAM changes;
  - changes to frozen protocols.
- **Decisions:** for any key product decision, recommend and wait for the user's approval.

## 15. Deliverables and success criterion
- **Deliverables:**
  - the Next.js app;
  - the DAG editor;
  - the Bedrock planner and chatbot;
  - the Library;
  - the Auditor MVP;
  - XAI and evidence panels;
  - tests;
  - architecture docs;
  - setup and deploy instructions;
  - a status report.
- **Success, two users:**
  - One user describes a data-science problem, generates a workflow, sees it on the canvas, edits it by
    hand or by chat, reviews evidence-backed recommendations, and saves it.
  - Another user imports a workflow, inspects it, finds structural problems, explores improvements, and
    keeps control of every change.
