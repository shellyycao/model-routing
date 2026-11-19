# Model routing and workflow evaluation

Which LLM suits which step of a data-science workflow (clean → analyze → report), does mixing models beat using one,
and can a router's explanations and predictions be trusted? Real Bedrock runs, sandboxed code execution, frozen
scoring rules, and cost counted as part of the evaluation.

**中文简介：** 我同时用多个 AI，但选哪个、怎么搭配凭经验。这个项目用真实运行结果测三件事：Q1 各模型擅长什么；Q2 多模型接力是否优于单模型；Q3 路由器的解释和预测是否可信。成本也算评价。详细结果见 [docs/RESULTS_REPORT.md](docs/RESULTS_REPORT.md)（中文）。

## Findings in brief

- **Q1:** no model is best at every stage; many apparent failures are one recurring serialization bug or overly strict scoring, not inability.
- **Q2:** mixing is not reliably better. In the price-matched group the apparent advantage disappears after correction (single 6/12 vs mixed 46/96).
- **Q3:** explanations are computationally faithful, but feasibility predictions show no skill beyond trivial baselines (always-"no change" is at least as accurate in 7 of 8 cells).
- **Cost:** unit price is misleading (a reasoning model costs ~4.5x at the same price); cost per feasible completion was about $0.27 and $0.38 for the two model groups.

Small sample (4 synthetic projects), one workflow shape, exploratory. Frozen official results are never edited; post-hoc corrected views are shown beside them and labeled.

## Where to look

| What | File |
|---|---|
| Detailed results (motivation, method, results, limits) | [docs/RESULTS_REPORT.md](docs/RESULTS_REPORT.md) |
| Full report with sources for every number and a verification guide | [docs/FINAL_REPORT.md](docs/FINAL_REPORT.md) |
| Provenance of this snapshot | [PROVENANCE.md](PROVENANCE.md) |
| Frozen protocols and amendments | `docs/*PROTOCOL*.md`, `docs/*AMENDMENT*.md` |
| Code | `src/` (Bedrock client, workflow, routing), `experiments/` (runners, analyses), `tests/` |
| Raw and processed results | `results/raw/`, `results/processed/`, `results/reports/` |
| Demo site | `web/` (Next.js) |

## Reproduce (offline, no model calls)

```bash
python -m venv .venv && .venv/bin/pip install -e .
.venv/bin/python -m pytest -q
.venv/bin/python -m experiments.verify_frozen_hashes
```

Paid runs need AWS Bedrock access and are locked behind a frozen manifest, git tag and explicit approval; they are not needed to verify the analyses.
