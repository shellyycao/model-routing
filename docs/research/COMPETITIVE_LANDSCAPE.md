# Competitive Landscape: Explainable Model / Workflow Routing

Scan date: 2026-11-19. This landscape changes quickly, so re-check product docs before quoting this externally.
Legend: **[V]** = verified against the cited primary source (URL in the table or in Sources). **[U]** = unclear or not found in the docs reviewed. "Not found" means only that the docs reviewed did not show it; it does not prove the product lacks the feature.

## Summary

- **Most commercial routers only expose *which* model was picked.** This holds for Bedrock Intelligent Prompt Routing, Azure Foundry model router, Not Diamond and Martian [V; Martian per third-party spec]. A few now also say *why*. OpenRouter's Jev/Auto Router returns a `reason` field and a free-text `summary` [V]. LiteLLM's auto-router logs `cause`, `tier`, a heuristic `score` and `signals`, and classifier probabilities [V].
- **No router or workflow builder we reviewed checks its stated reasons or predictions against outcomes.** LiteLLM's docs even say its classifier confidences describe the choice and are "not independently measured correctness" [V]. Its "savings" figure is cost against a counterfactual baseline that "does not predict alternate model responses" [V].
- **Workflow builders do not recommend models.** In Dify, n8n and CrewAI the user picks the model for each node or agent, or writes rules for it. n8n's Model Selector is first-match-wins rules [V]. Model recommendation and explanation were not found in the docs reviewed.
- **The closest academic work is Topaz** (Okamoto, Erol, Riedl; arXiv 2604.03527, Apr 2026) [V]. It routes each subtask of an agentic workflow, records a trace of skill-match scores and cost penalties, and turns that trace into explanations. Its framing is "auditability". The overlap is large, but there are three gaps:
  - Its explanations are **LLM-written** (Gemini) from the log, not template-bound [V].
  - It runs **no faithfulness evaluation** [V].
  - It does **no validation against executed outcomes**, and lists that as future work [V].
- **Routesplain** (arXiv 2511.09373, Nov 2025) [V] claims "faithful and intervenable" routing through a concept bottleneck. It checks faithfulness with concept ablation, interventions and synthetic counterfactual concept flips. It is single-query routing for software tasks, and it does not validate explanations against outcomes prospectively.
- **Commitment logging has a near-match.** A USPTO document titled "Explainable large language model routing with immutable audit trails" (No. 12596738) appears to log each routing choice with a human-readable explanation in a tamper-evident structure [title and snippet V; claims, assignee and dates U]. This undercuts any claim that "tamper-evident logging of routing explanations" is new. Have someone read the claims.
- **What we found no prior work on:** measuring *both* faithfulness and empirical validity of counterfactual routing explanations, with the predictions committed *before* outcomes are known, and reporting the gap between the two (100% vs. 44% here). XAI work on recommenders scores counterfactual "fidelity" against the *model*, not against real-world outcomes [V]. Karimi et al. (2020) formalized the gap between counterfactual explanations and real interventions [V], but not for LLM routing.

## Product table

| Product | Recommends / routes | Explains? How | Validates explanations or predictions vs. outcomes? | Source |
|---|---|---|---|---|
| OpenRouter Auto / Jev Router | Model and reasoning effort per request | **Partly** [V]. With opt-in metadata it returns `candidates` (tier, `estimated_cost`), `resolved_models` and a `reason` ("the policy's reason"). General router metadata has a free-text `summary` one-liner. How `reason` is generated is [U]. | Not found. In-session signals (repeated errors, failing tests) trigger model switches [V], but no stated-reason vs. outcome check. | openrouter.ai/docs/guides/routing/routers/jev-router.md; /features/router-metadata.md; /routers/auto-router.md |
| LiteLLM auto-router (complexity / semantic / adaptive) | Tier to model | **Yes, structured** [V]. Decision log has `cause=`, `tier`, heuristic `score`, `signals`, `routed_model`. JEV decisions add `classifier_probabilities` and `classifier_confidence`. A `test_routing` dry-run endpoint exists. | **No** [V]. Docs say the confidences are "not independently measured correctness." The adaptive mode uses Thompson sampling on rewards, but the reward is not defined on the page [U]. | docs.litellm.ai/docs/proxy/auto_routing |
| Not Diamond | Model per prompt (pretrained or custom router) | Not found. Gives a session ID and the chosen model only [V]. | Not found. Custom routers are trained on your eval data [V]. | docs.notdiamond.ai/docs/key-concepts |
| Amazon Bedrock Intelligent Prompt Routing | 2 models in one family, based on predicted quality | **Rule-level only** [V]. User sets a "response quality difference" threshold; trace returns the invoked model ID. | Not found. Docs say it "can't adjust routing decisions … based on application-specific performance data" [V]. | docs.aws.amazon.com/bedrock/latest/userguide/prompt-routing.html |
| Azure Foundry model router | Model per prompt (small ML router) | Not found. `response.model` plus Azure Monitor metrics per model [V via search summary of MS Learn]. | Not found | learn.microsoft.com/azure/foundry/openai/concepts/model-router |
| Martian | Model per prompt | Markets "model mapping" interpretability [V, press]. Per-request explanation not found; response `model` field per third-party API spec [U]. | Docs benchmarking page returned 404 [U] | techcrunch.com 2023-11-15; docs.withmartian.com |
| Unify | Model / endpoint via custom quality-cost-latency metric | Weighted-sum metric syntax (transparent objective); per-request rationale not found [V/U] | Router trained on Unify's benchmarks; outcome validation not found | docs.unify.ai/routing/routing_syntax |
| RouteLLM (OSS) | Strong vs. weak model | Numeric win-rate threshold only [V] | Offline benchmark eval (MMLU, GSM8K, MT-Bench) [V] | github.com/lm-sys/RouteLLM |
| n8n Model Selector | User-written rules, first match wins | The rules are the explanation; no recommendation [V] | No | docs.n8n.io/.../n8n-nodes-langchain.modelselector/ |
| Dify | User picks model per LLM node | Not found; docs give selection guidance in prose only [V] | Not found | docs.dify.ai/en/use-dify/nodes/llm |
| CrewAI | User picks LLM per agent; optional planning LLM | Planning LLM writes plans (LLM text), not model recommendations [V] | A Testing page existed in v0.51 docs; content not reviewed [U] | docs.crewai.com/en/concepts/planning |
| LangGraph / Flowise / AutoGen | Orchestration frameworks | Not reviewed in depth: no model recommendation found [U] | [U] | n/a |
| Observability (Langfuse, Braintrust, Galileo) | Per-step cost and quality tracing | Post-hoc analytics, not routing explanations [V, vendor round-up only] | Measures outcomes, but does not check router-stated reasons | fast.io round-up (secondary) |

## Literature table

| Work | Setting | Explanation | Faithfulness check | Outcome or counterfactual validation |
|---|---|---|---|---|
| FrugalGPT (Chen, Zaharia, Zou 2023) [V] | LLM cascade | None | none | Benchmark accuracy and cost |
| Hybrid LLM (Ding et al. 2024, ICLR) [V] | 2-model routing | Quality-gap score | none | Benchmark |
| RouteLLM (Ong et al. 2024, ICLR'25) [V] | Strong/weak routing | Win-rate threshold | none | Benchmark |
| IRT-Router (Song et al., ACL 2025) [V] | Multi-LLM routing | "Interpretable" ability and difficulty parameters | Not found | Benchmark (20 LLMs, 12 datasets) |
| MasRouter (Yue et al., ACL 2025) [V] | Multi-agent: mode, role and LLM per agent | None found | none | Benchmark |
| AgentRouter (arXiv 2609.22951, Sep 2026) [V] | Per-step tier routing in agent trajectories | 5-feature classifier; no explanations found | none | Benchmark |
| AgentOpt v0.1 (arXiv 2604.06296, Apr 2026) [V] | Model per role in an agent pipeline (search) | Not found in abstract | none | Measured accuracy and cost on 4 benchmarks |
| AFlow (2410.10762), ADAS (2408.08435), DSPy (2310.03714) [V] | Automatic workflow or pipeline optimization | None found (outputs are code or programs) | none | Execution feedback used for *optimization*, not explanation validation |
| BELLA "Trust by Design" (arXiv 2602.02386, Feb 2026) [V] | Skill-profile, cost-aware single-query selection | NL rationales; generation method not stated | **None** | Proposed, not reported |
| **Routesplain** (Štorek et al., Oracle/Columbia, arXiv 2511.09373, Nov 2025) [V] | Single-query routing, software tasks | Concept bottleneck; concepts are user-editable | Concept ablation and gold-concept intervention | Synthetic counterfactual concept flips (selection shift). Router scored on stored execution outcomes. No prospective prediction-vs-outcome check. |
| **Topaz** (Okamoto, Erol, Riedl, Georgia Tech, arXiv 2604.03527, Apr 2026) [V] | **Per-subtask routing in a 6-stage agentic workflow**, budget DP and multi-objective | **LLM-generated (Gemini) from a structured routing log** | **None reported** (one case study) | **None.** Sensitivity sweeps only; outcome monitoring is future work |
| Jacovi & Goldberg 2020 (ACL) [V] | XAI theory | n/a | Defines faithfulness vs. plausibility | n/a |
| Karimi, Schölkopf, Valera 2020 [V] | Algorithmic recourse | Counterfactual explanations | n/a | Argues counterfactual explanations ≠ real interventions (closest conceptual precedent for "empirical validity") |
| Recsys counterfactual fidelity (Baklanov et al. SIGIR'25; SPINRec arXiv 2511.18047; IJCAI'26 top-k protocols) [V via abstracts] | Recommender XAI | Feature attributions | Counterfactual perturbation fidelity *against the model* | No real-world outcome validation |
| "Learning What to Skip" (arXiv 2609.30734) [V via abstract] | Multi-agent workflows | n/a | n/a | Counterfactual stage-skip interventions for *credit assignment*, not explanations |

## Closest prior work

1. **Topaz (arXiv 2604.03527)** is the closest overall: explainable per-stage model routing for agentic workflows, with explanations built from a recorded routing trace, framed as auditability. Our differences:
   - Our explanations are template-bound to trace fields; Topaz uses an LLM to write them.
   - We check faithfulness mechanically (claim-by-claim checks and router replay).
   - We commit counterfactual predictions before execution and validate them against executed outcomes.
2. **Routesplain (arXiv 2511.09373)** is the closest on the *faithfulness* claim. It is faithful by construction (concept bottleneck) and tests counterfactuals on the router's behaviour. It does not test whether the predicted consequences hold in the world. It covers single queries, not workflows.
3. **USPTO 12596738**, "Explainable LLM routing with immutable audit trails", is the closest on *tamper-evident logging of routing explanations*. Claims, assignee and status are [U]: the PDF is a scanned image we could not read.

Honourable mentions:
- BELLA (2602.02386), which shares authors with Topaz.
- OpenRouter Jev Router's `reason` field and LiteLLM's `cause`/`score` decision logs: shipping products that do expose structured reasons.

## Verdict and recommended wording

**Well supported:**
- No router or workflow tool we reviewed validates its explanations or counterfactual predictions against executed outcomes.
- No academic routing paper we found measures *empirical validity* of explanations separately from faithfulness, or pre-commits predictions before outcomes.
- Reporting a large gap between the two (100% vs. 44%) appears new and is a scientifically interesting result in its own right.

**Overstated or risky:**
- **"Some give reasons" undersells the field.** OpenRouter (`reason`, `summary`) and LiteLLM (`cause`, `score`, probabilities) expose structured decision records today. Topaz explains per-stage workflow routing from traces.
- **"Almost none let you verify whether reasons can be trusted" is ambiguous.** Routesplain *does* let you verify faithfulness (ablation, intervention). LiteLLM's structured logs are partially checkable. The defensible claim is about *outcome* validation, not "trust" in general.
- **Do not claim novelty for:**
  - trace-grounded explanations (Topaz);
  - faithful router explanations as a concept (Routesplain);
  - tamper-evident logging of routing explanations (USPTO 12596738, pending a read of its claims).
- **The novelty is the combination plus the evaluation protocol**, not any single component.
- **The landscape moves monthly.** Topaz, AgentRouter and Jev Router all appeared in 2026.

**Recommended wording:**

> "Model routers increasingly report *which* model they chose and, sometimes, *why*. Research systems such as Topaz and Routesplain ground those reasons in the router's own computation. To our knowledge, none checks whether the reasons *predict what actually happens*. We separate two properties: **computational faithfulness** (every number in the explanation is bound to, and replayable from, the router's decision trace) and **empirical validity** (counterfactual 'what-if' predictions, committed to a tamper-evident log before execution, are scored against executed outcomes). In our benchmark, explanations were 100% faithful but only 44% valid on feasibility direction. Faithful explanations can still be wrong about the world."

Shorter tagline: *"Faithful is not the same as correct: we pre-register our router's what-if predictions and score them against what actually happened."*

Qualify every "first" claim with "to our knowledge, as of Nov 2026".

## Sources

Products:
- https://openrouter.ai/docs/guides/routing/routers/jev-router.md
- https://openrouter.ai/docs/guides/features/router-metadata.md
- https://openrouter.ai/docs/guides/routing/routers/auto-router.md
- https://docs.litellm.ai/docs/proxy/auto_routing
- https://docs.notdiamond.ai/docs/key-concepts
- https://docs.aws.amazon.com/bedrock/latest/userguide/prompt-routing.html
- https://learn.microsoft.com/azure/foundry/openai/concepts/model-router
- https://docs.unify.ai/routing/routing_syntax
- https://github.com/lm-sys/RouteLLM
- https://techcrunch.com/2023/11/15/martians-tool-automatically-switches-between-llms-to-reduce-costs/
- https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.modelselector/
- https://docs.dify.ai/en/use-dify/nodes/llm
- https://docs.crewai.com/en/concepts/planning.md
- https://fast.io/resources/best-ai-agent-cost-optimization-tools/ (secondary)

Papers:
- Topaz: https://arxiv.org/abs/2604.03527
- Routesplain: https://arxiv.org/abs/2511.09373
- BELLA: https://arxiv.org/abs/2602.02386
- IRT-Router: https://aclanthology.org/2025.acl-long.761
- MasRouter: https://arxiv.org/abs/2502.11133
- AgentRouter: https://arxiv.org/abs/2609.22951
- AgentOpt: https://arxiv.org/abs/2604.06296
- FrugalGPT: https://arxiv.org/abs/2305.05176
- RouteLLM: https://arxiv.org/abs/2406.18665
- Hybrid LLM: https://arxiv.org/abs/2404.14618
- AFlow: https://arxiv.org/abs/2410.10762
- ADAS: https://arxiv.org/abs/2408.08435
- DSPy: https://arxiv.org/abs/2310.03714
- Jacovi & Goldberg: https://arxiv.org/abs/2004.03685
- Karimi et al.: https://arxiv.org/abs/2002.06278
- SPINRec: https://arxiv.org/abs/2511.18047
- Learning What to Skip: https://arxiv.org/abs/2609.30734

Patent:
- https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/12596738 (title from the search index; the scanned PDF was not machine-readable)
