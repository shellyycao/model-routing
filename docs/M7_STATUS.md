# M7 website status

**Date:** 2026-11-19 · **Scope:** M7.1 foundation plus safe scaffolding for M7.2–M7.4 · **Owner:** Frontend Engineer (`web/`)
**Paid calls:** none · **Deployment:** none · **Credentials:** none used or stored

Product brief: `docs/M7_WEBSITE_HANDOFF.md`. Visual reference: `docs/design/modelflow_canvas_first_copilot.html`. Setup and deploy steps: `web/README.md`.

## What works

| Area | State |
|---|---|
| Home (`/`) | Approved headline; *Create a workflow* prompt with **Generate Workflow** and three example prompts; *Improve my workflow*: open saved, import JSON/YAML (previewed before applying), empty canvas |
| Studio (`/studio`) | React Flow DAG editor: add stages (source, task, merge, output), rename, delete (Backspace/Delete or panel), drag, connect via handles, fan-out, fan-in, parallel branches, cycle/self-loop/duplicate rejection, edge delete, edge reconnect, zoom/pan/fit, undo/redo (buttons + ⌘/Ctrl+Z, ⌘/Ctrl+Shift+Z, Ctrl+Y), JSON and YAML export, save as version. Banner: “Visual design — not necessarily executable” |
| Stage fields | Name, description, task type, assigned model, inputs, outputs, merge rule (when fan-in), optional execution config (stored only), dependencies shown |
| Model dropdown | Unassigned, Claude Sonnet 4.6, Amazon Nova Pro, gpt-oss-120b, Kimi K3, GLM 5, Custom (unverified). No Grok. Examples and templates never pre-assign a model |
| Workflow module | Pure TS: `schemaVersion: 1` schema + parser (also reads the prototype's `{label,x,y,from,to}` shape), validation (duplicate node/edge ids, duplicate edges, dangling edges, self-loops, cycles, disconnected stages), JSON/YAML import/export, history, typed edit actions, diff |
| Library (`/library`) | localStorage behind the async `WorkflowStore` interface: save, reopen, rename, duplicate, delete (confirmed), version history (max 50 per workflow), restore-as-new-version, export |
| Planner scaffolding | `PlannerProvider`/`ChatProvider` interfaces; `/api/plan` and `/api/chat` route handlers using deterministic **mock** providers (no network). Drafts are previewed **on the canvas only** with Apply / Edit / Discard; applying is undoable. Labels: “Template draft (mock planner) — not AI-generated yet”, “Rule-based reply (mock assistant) — not AI-generated yet” |
| Ask ModelFlow | Floating button opens a docked side panel (does not cover the canvas). Mock commands: add [after/before], parallel branch, remove, rename, connect, review. Proposals come back as typed actions; the client re-validates them against the current graph before previewing |
| Auditor | Deterministic checks: entry/terminal stages, multiple entries, disconnected, cycles, invalid structure, unassigned/custom/unknown models, fan-in without a merge rule, unsatisfied declared inputs, connections passing nothing declared, possible duplicates. Separate “Evidence-based recommendations” section: empty, status *Unverified* |
| Evidence | `EvidenceStatus` (`Directly tested` / `Partially supported` / `Unverified`) and result-kind labels (measured, prediction, retrospective oracle, post-hoc, insufficient evidence). `/evidence` page and a per-stage “Why this model?” panel showing only copied numbers, each with source path, field, version and sha256. Every stage is shown as *Unverified for this stage* |
| Evidence copy | `web/scripts/build-evidence.mjs` copies 9 price-matched-v2 cells and 27 pooled three-stage paths into `web/public/evidence/summary.json`; a test checks the hashes and each value against the source files |

### Prototype issues fixed

- Template output is labelled as a mock template draft, never “AI draft”.
- Example patterns and templates leave every model “Unassigned”.
- The Home subtitle no longer claims “evidence-backed AI recommendations” (see decision 1).
- There is one preview location: the canvas (chat only links to it).
- Styles are defined once (Tailwind theme tokens + one component layer); no duplicated CSS blocks.
- At 800 px width the left palette collapses to icons and the side panel docks beside the canvas (canvas ≈ 444 px wide with chat open).

## Routes worth screenshotting

`/` · `/studio?pending=1` right after Generate Workflow (draft preview with diff badges) · `/studio` with the Ask panel open and a proposed edit shown on the canvas · Studio *Review* tab · Studio *Evidence* tab with a tested model assigned · `/library` with History expanded · `/evidence`.

## Test and build results (2026-11-19)

| Check | Result |
|---|---|
| `npm test` (Vitest 4.1.12) | **7 files, 50 tests passed, 0 failed** |
| `npm run lint` | 0 errors, 0 warnings |
| `npm run typecheck` | passes |
| `npm run build` (Next 16.4.6) | passes; `/`, `/studio`, `/library`, `/evidence` static; `/api/plan`, `/api/chat` dynamic |
| Playwright smoke test | **Skipped**: it needs a ~150 MB browser download; the flows were checked manually in a browser instead (generate → preview → apply/edit → chat proposal → undo/redo → save → reopen → library duplicate/history → evidence) |
| Repo `pytest -q` (main checkout venv, run in this worktree) | 527 passed, 8 skipped, **8 failed**, none in files this work touched (Docker timeout test, frozen-tag test, and `dataset_tree_sha256` checks in the price-matched suites). Needs checking in the main checkout |

## Stubbed or not done

- **Real planner and chat (M7.2/M7.3):** `BedrockPlannerProvider` / `BedrockChatProvider` throw “Bedrock provider not enabled — requires user-approved budget”. No SDK, no credentials, no streaming.
- **Evidence-based recommendations (M7.4):** none yet. The section exists and says so.
- **What-if / cost estimates per stage:** not implemented, deliberately. There are no estimates for user DAGs.
- **Plain-English “describe your existing workflow”** import goes through the mock planner, not a parser.
- **Persistence:** browser-only; cloud store not implemented (the interface is ready for one).
- **Drag-and-drop toast for invalid connections:** invalid targets are blocked and the handle turns red, but the explanatory toast did not appear in automated drag testing; worth a manual check.
- **Arrow-key node moves** are not recorded as separate undo steps; they are folded into the next edit's undo step.

## Open product decisions for the user

1. **Home subtitle:** the approved line promises “evidence-backed AI recommendations”. It is softened until recommendations exist. Restore it when M7.4 ships?
2. **Planner/chat model:** which Bedrock model (for example Claude Sonnet 4.6 for quality, or GLM 5 for cost; both are in the saved price-matched results), and in which region?
3. **Per-request limits:** proposed starting point to confirm: ≤ 4,000 input and ≤ 2,000 output tokens per planner call; ≤ 2 bounded retries; chat history capped at the last N turns.
4. **Invocation caps and dev/test budget:** a per-day call cap and a total development budget (with a hard ledger cap like the research runs).
5. **Streaming** for `/api/chat`: yes or no for M7.3.
6. **Hosting:** Vercel preview deployment with root `web/`, and when (needs approval; no public deploy yet).
7. **Cloud persistence/accounts:** stay local-only for the MVP?

## How to run locally

```bash
cd web
npm ci
npm run dev          # http://localhost:3000
npm test && npm run lint && npm run build
npm run evidence     # only to refresh public/evidence/summary.json from results/processed
```
