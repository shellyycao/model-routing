# Which LLM Should I Use for My Task?

An empirical study of model choice in multi-step AI workflows. Real AWS Bedrock runs, sandboxed code execution,
fixed automatic checks, and cost counted as part of the evaluation.

**Live demo:** [modelflow-alpha.vercel.app](https://modelflow-alpha.vercel.app) · **Poster:** [poster/poster.pdf](poster/poster.pdf)

**中文简介：** 我们都有自己常用的 AI 模型，但选哪个、怎么搭配往往凭经验。这个项目用真实运行结果回答三个问题：Q1 各模型擅长哪一步；Q2 多模型接力是否优于单模型；Q3 路由器的解释和预测是否可信。成本也作为评价的一部分。详细中文结果见 [docs/RESULTS_REPORT.md](docs/RESULTS_REPORT.md)。

## Why this matters

People increasingly chain several AI models into one workflow, and tools now recommend which model to use for each
step, often with an explanation attached. This project treats those recommendations as a **Responsible AI
evaluation problem**:

- **Explainable AI (XAI):** an explanation can be *faithful* (it honestly describes how the system decided) and still
  be *wrong about the world*. This project measures both properties separately for the same router.
- **AI evaluation:** single-model benchmarks may not predict how models behave once chained together. Here every
  combination is actually run, and success is judged on the end-to-end output.
- **Human-AI interaction:** a fluent, faithful-sounding explanation can make people trust a recommendation more than
  its track record justifies. The finding that the router's explanations are faithful but its predictions lose to a
  constant guess is a concrete case of that risk.

## Related work

- **Commercial routers** (OpenRouter, LiteLLM, Not Diamond, Amazon Bedrock Intelligent Prompt Routing, Azure Foundry
  model router, Martian, Unify) and open-source **RouteLLM** pick a model per request. Most report only *which*
  model was chosen; a few report *why*. None of the docs reviewed check the stated reasons or predictions against
  real outcomes. Workflow builders (Dify, n8n, CrewAI) leave model choice to the user.
- **Topaz** (Okamoto, Erol, Riedl, arXiv 2604.03527) routes subtasks of agentic workflows and explains choices from
  a trace, but its explanations are LLM-written and it does not evaluate faithfulness or validate against executed
  outcomes. **Routesplain** (arXiv 2511.09373) tests faithfulness with concept interventions for single-query routing,
  not against real downstream outcomes.
- **XAI faithfulness:** Jacovi & Goldberg (2020) separate faithfulness (does the explanation reflect the model's
  reasoning?) from plausibility. Karimi et al. (2020) distinguish counterfactual explanations from real
  interventions. This project applies that distinction to LLM routing: explanations are checked for faithfulness
  against the router's computation, and its counterfactual predictions are checked against executed runs.
- **Over-reliance on explanations:** Bansal et al. (CHI 2021) found that AI explanations can increase acceptance of
  AI recommendations whether or not they are correct.

**Contribution:** to our knowledge, this is the first evaluation that measures *both* the faithfulness and the
empirical validity of a model router's counterfactual explanations, with predictions committed before outcomes were
known, and that reports the gap between them (100% faithful vs. below a constant baseline). It also compares mixed
and single-model workflows on cost and success together. Full product-by-product comparison with sources:
[docs/research/COMPETITIVE_LANDSCAPE.md](docs/research/COMPETITIVE_LANDSCAPE.md).

## Research questions

| | Question |
|---|---|
| **Q1** | Which model is good at which step (clean, analyze, report)? |
| **Q2** | Does mixing models across steps beat using one model throughout? |
| **Q3** | Can a model router's explanations and predictions be trusted? |
| **Cost** | Which workflow is worth its cost, not just which one succeeds? |

## How it was tested

- **4 synthetic data-science projects** (customer churn, energy consumption, retail sales, support operations), each a
  3-step workflow: **Clean → Analyze → Report**. Synthetic data gives every step a known correct answer.
- **Two model groups of 3 Bedrock models each.** Every model ran every step alone and in every combination
  (3 × 3 × 3 = 27 workflows per project):
  - Group 1: Claude Sonnet 4.6, Amazon Nova Pro, gpt-oss-120b
  - Group 2 (price-matched): Claude Sonnet 4.6, Kimi K3, GLM 5
- **Success** means the final output passes fixed automatic checks. Total spend is recorded for every run,
  including failed ones.
- **A router** recommends model swaps and explains its choices. Its explanations are checked against its own
  computation, and its predictions are checked against real outcomes.

## Findings

### Q1: strengths depend on the step

![Stage success by model](poster/charts/q1_stage_success.png)

In Group 1 no model was best at every step. Kimi K3 passed cleaning on all 4 projects but reporting on only 1.
Nova Pro failed cleaning and analysis on all 4 but passed 2 reports. In Group 2, GLM 5 passed every step on all 4
projects (its 4 analysis failures under the original labels were all one data-type serialization error).
Pick a model for the step, not by its overall reputation.

### Q2: mixing models is not reliably better

![Single vs mixed workflows](poster/charts/q2_single_vs_mixed_final_only.png)

Group 2: single-model workflows 50% vs mixed 48%. Group 1: 17% vs 24%, both low. Errors in an early step carry into
later ones, so a workflow is only as strong as its weakest step and has to be tested as a whole.

### Q3: faithful explanations, no predictive skill

![Router vs baselines](poster/charts/q3_router_vs_baselines.png)

All 880 of 880 explanation sentences match the router's own computation. But its predictions of whether a swap helps
are right 42% (Group 1) and 38% (Group 2) of the time, while always guessing "no change" gets 52% and 56%.
A clear explanation is not the same as a correct prediction.

### Cost: same success, very different cost

![Cost vs success](poster/charts/cost_vs_success_two_groups.png)

| Group | Workflow (clean → analyze → report) | Avg cost per run | Projects passed |
|---|---|---|---|
| 1 | gpt-oss → gpt-oss → Nova | $0.010 | 3/4 |
| 1 | Sonnet → gpt-oss → Nova | $0.068 | 3/4 |
| 1 | Sonnet only | $0.145 | 2/4 |
| 2 | GLM only | $0.022 | 4/4 |
| 2 | GLM → Sonnet → GLM | $0.056 | 4/4 |
| 2 | Sonnet only | $0.144 | 1/4 |

Two workflows can reach the same success at very different prices, and the most expensive model is not the most
successful. Whether to switch models depends on cost as well as success.

An additional independent benchmark covers three other tasks (debugging, structured extraction, literature ranking);
see Part A of [docs/FINAL_REPORT.md](docs/FINAL_REPORT.md).

## Design decisions

| Decision | Why |
|---|---|
| Synthetic projects with planted issues | Every step has a known correct answer, so success can be checked exactly and automatically. |
| Fixed automatic checks instead of an LLM judge | Avoids one model grading another; the same output always gets the same score. |
| Run every combination, not a sample | Q2 compares mixed and single-model workflows on the same projects, with no selection bias. |
| Protocols and scoring rules frozen before results | Prevents tuning the analysis to the results. Frozen files are never edited; later changes are separate amendments. |
| Leave-one-project-out routing | The router never sees the project it is making a recommendation for. |
| Template-based explanations from a decision trace | Every sentence can be checked against the router's actual computation, unlike free-text LLM explanations. |
| Predictions saved to a hash-chained log before outcomes were checked | Predictions cannot be rewritten after the fact. |
| Constant baselines next to the router | A router is only useful if it beats "always predict no change". |
| Code runs in an isolated Docker sandbox | Model-written code cannot touch the host or the network. |
| Cost recorded for every call, including failures | Cost is part of the result, and a hard budget cap stops runs automatically. |

## Stakeholders and risks

- **Practitioners choosing models:** benefit from evidence over reputation, but should not treat 4 projects as a
  general ranking of these models.
- **Router and tool builders:** an explanation that is faithful to the code says nothing about whether the advice is
  right. Recommendations should be validated against outcomes and compared with trivial baselines before deployment.
- **End users of AI recommendations:** risk over-trusting fluent explanations. This router should not be deployed
  as-is: its predictions do not beat a constant guess.
- **Cost-driven decisions:** choosing the cheapest workflow can hide quality loss; this project reports success and
  cost together for that reason.
- **Misuse:** single-run results could be quoted as "model X is better than Y". The reports label every number as
  pre-registered or post-hoc and avoid causal or provider-wide claims.

## Limitations

- 4 synthetic projects, and most workflow paths were run once.
- Only models available on AWS Bedrock to this account were tested.
- The two groups used different output-token limits (4096 vs 16384), so they are not directly comparable.
- Success is judged by fixed automatic checks. Some results were re-labeled after the experiments under rules
  committed in advance. The original (frozen) results are never edited, and both views are reported side by side
  in [docs/FINAL_REPORT.md](docs/FINAL_REPORT.md). The charts above show the re-labeled values.

## Next steps

- Test more workflows, models, and real projects, with repeated runs.
- Retrain the router so it beats simple baselines.
- Build a tool that recommends workflows by success and cost.

## Repository guide

| What | Where |
|---|---|
| Guide to the docs folder (which files to read first) | [docs/README.md](docs/README.md) |
| Full report: every number with its source, plus a verification guide | [docs/FINAL_REPORT.md](docs/FINAL_REPORT.md) |
| Literature and product comparison | [docs/research/COMPETITIVE_LANDSCAPE.md](docs/research/COMPETITIVE_LANDSCAPE.md) |
| Results write-up in Chinese | [docs/RESULTS_REPORT.md](docs/RESULTS_REPORT.md) |
| Experiment protocol, amendments, and post-hoc rules | `docs/*PROTOCOL*.md`, `docs/*AMENDMENT*.md`, `docs/*RULES*.md` |
| Code: Bedrock client, workflow runner, routing | `src/` |
| Experiment runners and analyses | `experiments/` |
| Synthetic projects and ground truth | `datasets/` |
| Raw records, processed results, reports | `results/raw/`, `results/processed/`, `results/reports/` |
| Poster (PDF) | [poster/poster.pdf](poster/poster.pdf) |
| Poster charts and the script that draws them | `poster/charts/` |
| Tests | `tests/` |
| Demo site (Next.js) | `web/` |
| Provenance of this public snapshot | [PROVENANCE.md](PROVENANCE.md) |

## Reproduce the analyses (offline, no model calls)

Requires Python 3.11+.

```bash
python -m venv .venv && .venv/bin/pip install -e .
.venv/bin/python -m pytest -q
.venv/bin/python -m experiments.verify_frozen_hashes
.venv/bin/python -m experiments.analyze_router_relabel
.venv/bin/python -m experiments.analyze_failure_taxonomy
python3 poster/charts/make_charts.py
```

Every number above comes from the saved records in `results/`, so none of this needs an AWS account or costs money.

## Running new experiments (optional, paid)

New model runs need:

1. An AWS account with **Amazon Bedrock** access in `us-east-1`, and model access granted in the Bedrock console
   for the models in `configs/` (Claude Sonnet 4.6, Amazon Nova Pro, gpt-oss-120b, Kimi K3, GLM 5).
2. Credentials in an AWS profile (`~/.aws/credentials`), never in this repo. Copy `.env.example` to `.env` and set
   `AWS_PROFILE`, `AWS_REGION` and `MAX_BUDGET_USD` (a hard spend cap enforced by the cost ledger).
3. **Docker**, for the code-execution sandbox (`sandbox/`).

Tests that make real Bedrock calls are skipped unless `RUN_LIVE=1`. The original runner also checks for a frozen
git tag before paid runs; that tag is not in this public snapshot (see [PROVENANCE.md](PROVENANCE.md)).
No model weights are downloaded; all models are called through the Bedrock API.

## Demo website

`web/` is a Next.js prototype of a visual workflow builder ("ModelFlow") that displays the saved results. It makes
no model calls. Live version: **https://modelflow-alpha.vercel.app**. To run it locally (Node 20.9+):

```bash
cd web && npm ci && npm run dev    # http://localhost:3000
```

Details: [web/README.md](web/README.md).

## How this was built

Development used AI coding agents (Claude Code and OpenAI Codex) under the author's direction. The agent roles are
defined in `.claude/agents/`. Experiment protocols were frozen before results; agent work was checked at review
checkpoints by a separate read-only reviewer, and the reviews are kept in `docs/reviews/`. All research questions,
design choices and conclusions were approved by the author.

## Author and license

Shelly Cao, M.S. Interdisciplinary Data Science, Duke University. Released under the [MIT License](LICENSE).
