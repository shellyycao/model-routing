# ModelFlow web (M7)

Next.js (App Router) + TypeScript + Tailwind v4 + `@xyflow/react` front end for ModelFlow:
a visual workflow studio, a local workflow library, mock planner/chat scaffolding and
read-only evidence panels built from saved research results.

**Nothing in this app calls a model.** The planner and the "Ask ModelFlow" assistant are
deterministic mocks, and their output is labelled that way. The Bedrock provider is a stub
that throws `Bedrock provider not enabled — requires user-approved budget`.

## Local setup

Requires Node 20.9+ (tested with Node 26) and npm.

```bash
cd web
npm ci             # exact versions from package-lock.json
npm run dev        # http://localhost:3000
```

| Command | What it does |
|---|---|
| `npm run dev` | Development server |
| `npm run build` | Production build (must pass) |
| `npm start` | Serve the production build |
| `npm run lint` | ESLint (next/core-web-vitals + typescript) |
| `npm run typecheck` | `tsc --noEmit` |
| `npm test` | Vitest unit tests (graph validation, import/export, history, edit diffs, persistence, auditor, mock providers, evidence integrity) |
| `npm run evidence` | Re-copy the evidence summary from `../results/processed/` |

## Routes

| Route | Purpose |
|---|---|
| `/` | Home: *Create a workflow* (goal prompt → Generate Workflow) and *Improve my workflow* (open saved, import JSON/YAML, empty canvas) |
| `/studio` | Canvas editor. `?id=<workflowId>` opens a saved workflow; `?new=1` starts empty; `?pending=1` previews a draft handed over from Home |
| `/library` | Saved workflows: open, rename, duplicate, version history, restore, export, delete |
| `/evidence` | Read-only tables copied from `results/processed/` with source path, version and hash |
| `POST /api/plan` | `{ goal }` → template draft from the mock planner |
| `POST /api/chat` | `{ message, context: { page, workflow, selectedNodeId } }` → reply + optional typed edit proposal from the mock assistant |

## Code layout

```
src/lib/workflow/   schema (versioned, schemaVersion: 1), graph helpers, validation,
                    JSON/YAML import-export, undo/redo history, typed edit actions + diff,
                    layered layout, example patterns          (framework-free, unit-tested)
src/lib/storage/    WorkflowStore interface + LocalWorkflowStore (localStorage / memory)
src/lib/auditor/    deterministic structural checks; evidence recommendations kept separate
src/lib/planner/    PlannerProvider / ChatProvider contracts, mock providers, Bedrock stub
src/lib/evidence/   EvidenceStatus, result-kind labels, summary.json types, formatting
src/components/     TopBar, ImportDialog, studio/* (canvas, panels, chat), evidence/*
scripts/            build-evidence.mjs (copies saved numbers; computes nothing new)
public/evidence/    summary.json (committed output of `npm run evidence`)
tests/              Vitest suites (fixtures are labelled SYNTHETIC_FIXTURE)
```

## Evidence summary

`npm run evidence` reads two committed files and writes `public/evidence/summary.json`:

- `results/processed/independent_v2/price_matched_v2_analysis.json` → `main_analysis_void_excluded.cells` and `pareto_frontier_by_task`
- `results/processed/workflow_cost_posthoc.json` → `prices`, `overall`, pooled rows of `pooled_path_summaries`, `limitations`

Each block records the source path, sha256 and analysis version. `tests/evidence.test.ts`
re-reads the sources (when present) and checks the hashes and every copied value. The output
is committed because a Vercel build of `web/` alone cannot see `../results`.

## Deploying to Vercel (not done — requires the user's go-ahead)

No `vercel.json` is needed. When approved:

1. In Vercel, import the repository and set **Root Directory** to `web`.
2. Framework preset: Next.js. Build command `npm run build`, install command `npm ci`.
3. No environment variables are required for the mock build. Do **not** add AWS credentials
   until a Bedrock budget is approved; when it is, add them as server-side environment
   variables only (never `NEXT_PUBLIC_*`) and set `MODELFLOW_PROVIDER=bedrock` once the
   provider is implemented.
4. Use a Preview deployment first; production/public deployment needs explicit approval.

## Limits of this build

- Workflows are visual designs; arbitrary DAGs are not necessarily executable and are never run.
- Library data lives in this browser's localStorage only.
- Evidence covers a task benchmark and a fixed three-stage workflow; it is never extrapolated
  to user DAGs, so every model choice is shown as *Unverified for this stage*.
