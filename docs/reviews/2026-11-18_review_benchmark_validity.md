# Review: benchmark validity, before any paid run (main @ eeb52d9)

- **Reviewer:** Research Reviewer (read-only, run as the built-in Plan agent following `.claude/agents/research-reviewer.md`)
- **Date:** 2026-11-18
- **Method:** read-only code inspection, plus in-memory probes. The reviewer monkeypatched the reference cleaning and analysis to inject plausible mistakes, and called `validate_reporting` on hand-made wrong reports. Nothing was written to disk.
- **Timing:** no model outcomes existed when this review was done. Changes adopted from it are therefore pre-registered, not post-hoc.

## Verdict

- The spec can be followed to the reference: independent pandas solutions pass all 3 projects.
- No ambiguous cleaning rules were found.
- Cleaning discriminates between models.

However:
- As configured, Experiment B cannot observe error propagation or interaction effects (B1).
- The reporting validator accepts several kinds of wrong report and rejects honest derived numbers (M1, M2).

## Findings

| ID | Severity | Finding | Proposed action | Status |
|---|---|---|---|---|
| B1 | BLOCKER | The cleaning gate requires an exact match, and the only failure policy terminates the path. So every analysis stage that runs sees input equal to the canonical file, and cleaning-error propagation can't be observed. Probes show it would be strong: a single plausible cleaning mistake makes 10–19 of about 20 analysis keys wrong. | Contracts v1.2: a pre-registered `continue_with_actual_artifact` policy. Strict feasibility is kept, and propagation accuracy is added. | **Awaiting user decision** |
| M1 | MAJOR | The reporting validator accepts wrong reports. Examples: wrong direction, correct numbers under the wrong group, example numbers from the question text exempted, coincidental matches in clustered values, wrong ranking, near-empty findings counted as covered. | Require `reported_values` for every required key; match per finding; remove "e.g." numbers from questions; add structured direction and ranking checks | **Awaiting user decision** |
| M2 | MAJOR | The reporting validator rejects correct reports: derived shares and deltas, cleaning counts, coarse rounding. | Whitelist recomputable derivations and cleaning-log counts, or demote `unsupported_claim_count` from gate to quality metric | **Awaiting user decision** |
| M3 | MAJOR | Ceiling risk: analysis prompts give near-transcription instructions on clean input, so feasibility is effectively binary. | Pre-register difficulty levers: keep `notes` out of prompts; add 1–2 derived-step questions per project; optional less-explicit spec tier; optional perturbed analysis input | **Awaiting user decision** |
| M4 | MAJOR | Some cleaning rules don't affect any finding, and duplicates are exact re-renderings, so dedup order never matters. | Add duplicates that differ in value; add questions using unread columns | **Awaiting user decision** |
| M5 | MAJOR | The three projects are near-identical templates, so leave-one-project-out tests a template rather than generalisation. | Add a structurally different 4th project (for example a two-file join or reshape) | **Awaiting user decision** |
| M6 | MAJOR | Validator details contain expected values. If they reach a model through a handoff or retry, ground truth leaks. | Models see only pass/fail | **Sent to the Workflow Engineer (in progress)** |
| m1 | MINOR | Canonical files and ground truth sit next to `raw.csv`. | Input allow-list; never render `project.json` `notes` | **Sent to the Workflow Engineer** |
| m2 | MINOR | A byte-order mark in the cleaned CSV header fails every check. | Strip it in the validator | Proposed benchmark fix |
| m3 | MINOR | The 1-cent tolerance is fragile at exactly one rounding unit. | Compare in integer cents, or use `abs_tol` 0.011 | Proposed benchmark fix |
| m4 | MINOR | numpy int64 values make `json.dump` fail, which may dominate differences between models. | Pre-register one identical prompt note for all models | Proposed (Workflow prompts) |
| m5 | MINOR | Reporting `quality_basis` defaults to ground truth even when the input is sandbox findings. | The caller must set it; covered in the Workflow brief | Noted |

## Not reviewed
- Prompts and orchestrator, which did not exist yet.
- Sandbox isolation (verified separately: `2026-11-18_sandbox_verification.md`).
- `datasets/generate.py` in detail.
- Model sampling settings.
- Behaviour under the sandbox's pandas 2.2.3. The probes used pandas 3.1.1 and stdlib only.
