"""A3 controlled literature corpus (SYNTHETIC; not live retrieval).

Documents are generated from structured facts (topic, method, dataset, metric, value, year). Relevance
labels are defined BY CONSTRUCTION for each query (topic + method):
  grade 2 = same topic AND same method; grade 1 = same topic, other method;
  grade 0 = hard negative (mentions the query's exact topic+method in a "prior work" sentence but studies a
            different topic) or unrelated. Relevant documents use paraphrased surface forms, so keyword overlap
            is not sufficient (checked by generate.py against a keyword baseline).
Each query gets 20 shuffled candidates: 4 grade-2, 5 grade-1, 6 hard negatives, 5 unrelated.
"""

from __future__ import annotations

import random

TOPICS = {
    "sepsis early warning": ("sepsis", "ICU vital signs"),
    "credit card fraud detection": ("fraud", "card transactions"),
    "crop yield forecasting": ("crop yield", "satellite imagery"),
    "short-term load forecasting": ("electric load", "smart-meter readings"),
    "customer churn prediction": ("churn", "subscription logs"),
    "hate speech moderation": ("hate speech", "social media posts"),
}
METHODS = {
    "gradient-boosted trees": "gradient boosting",
    "graph neural networks": "graph neural network",
    "transformer models": "transformer",
    "Bayesian hierarchical models": "Bayesian hierarchical model",
    "federated learning": "federated learning",
}
DATASETS = ["MIMIC-IV", "IEEE-CIS", "SentinelYield-2", "GEFCom", "ChurnBench", "HateCheck", "OpenGrid-5", "AgriSat"]
METRICS = ["AUROC", "F1", "MAPE", "accuracy"]
# Surface forms: documents describe topic/method with paraphrases, so relevance is semantic, not lexical.
TOPIC_FORMS = {
    "sepsis early warning": ["early detection of septic deterioration in intensive care", "sepsis early warning",
                             "predicting sepsis onset before clinical recognition"],
    "credit card fraud detection": ["identifying fraudulent payment-card activity", "credit card fraud detection",
                                    "flagging illegitimate card-not-present purchases"],
    "crop yield forecasting": ["predicting harvest output per hectare", "crop yield forecasting",
                               "season-ahead estimates of agricultural production"],
    "short-term load forecasting": ["day-ahead prediction of electricity demand", "short-term load forecasting",
                                    "hour-level forecasting of grid consumption"],
    "customer churn prediction": ["anticipating subscriber cancellations", "customer churn prediction",
                                  "estimating which customers will leave a service"],
    "hate speech moderation": ["detecting abusive and hateful online content", "hate speech moderation",
                               "automated screening of toxic posts targeting protected groups"],
}
METHOD_FORMS = {
    "gradient-boosted trees": ["boosted decision-tree ensembles", "gradient-boosted trees", "LightGBM-style additive tree models"],
    "graph neural networks": ["message-passing networks over relational graphs", "graph neural networks",
                              "learned node embeddings with neighbourhood aggregation"],
    "transformer models": ["self-attention sequence models", "transformer models", "attention-only encoder architectures"],
    "Bayesian hierarchical models": ["multilevel Bayesian models with partial pooling", "Bayesian hierarchical models",
                                     "hierarchical priors fitted by MCMC"],
    "federated learning": ["privacy-preserving training across institutions without pooling data", "federated learning",
                           "decentralised model updates aggregated on a server"],
}
SURNAMES = ["Okafor", "Lindqvist", "Tanaka", "Moreau", "Haddad", "Silva", "Novak", "Iyer", "Brennan", "Zhou"]


def _doc(rng, doc_id, topic, method, decoy=None):
    """decoy=(topic, method): mention them in a 'prior work' sentence WITHOUT studying them (hard negative)."""
    kw, data_desc = TOPICS[topic]
    m_kw = METHODS[method]
    t_form, m_form = rng.choice(TOPIC_FORMS[topic]), rng.choice(METHOD_FORMS[method])
    facts = {"topic": topic, "method": method, "dataset": rng.choice(DATASETS), "metric": rng.choice(METRICS),
             "value": round(rng.uniform(0.6, 0.97), 3), "year": rng.randint(2018, 2025),
             "first_author": rng.choice(SURNAMES)}
    title = f"{m_form[0].upper() + m_form[1:]} for {t_form}: {rng.choice(['an empirical study', 'a benchmark evaluation', 'lessons from deployment'])}"
    prior = (f"Prior work applied {decoy[1]} to {decoy[0]}; in contrast, " if decoy else "")
    abstract = (f"{prior}{'we' if prior else 'We'} address {t_form} with {m_form} on {data_desc}. Experiments on the {facts['dataset']} dataset "
                f"report {facts['metric']} of {facts['value']}. "
                f"{rng.choice(['We discuss calibration and drift.', 'We analyse failure cases.', 'We release code.'])}")
    return {"doc_id": doc_id, "title": title, "authors": f"{facts['first_author']} et al.", "year": facts["year"],
            "abstract": abstract, "facts": facts}


def build_cases(seed: int = 20261118, n_queries: int = 10) -> list[dict]:
    rng = random.Random(seed)
    combos = [(t, m) for t in sorted(TOPICS) for m in sorted(METHODS)]
    rng.shuffle(combos)
    cases, counter = [], 0

    def new_doc(topic, method, decoy=None):
        nonlocal counter
        counter += 1
        return _doc(rng, f"D{counter:04d}", topic, method, decoy)

    for qi, (topic, method) in enumerate(combos[:n_queries]):
        g2 = [new_doc(topic, method) for _ in range(4)]
        g1 = [new_doc(topic, rng.choice([m for m in METHODS if m != method])) for _ in range(5)]
        hard = [new_doc(rng.choice([t for t in TOPICS if t != topic]), rng.choice(list(METHODS)), decoy=(topic, method))
                for _ in range(6)]
        other = [new_doc(rng.choice([t for t in TOPICS if t != topic]), rng.choice([m for m in METHODS if m != method]))
                 for _ in range(5)]
        cands = g2 + g1 + hard + other
        rng.shuffle(cands)
        rel = {d["doc_id"]: 2 for d in g2} | {d["doc_id"]: 1 for d in g1} | {d["doc_id"]: 0 for d in hard + other}
        cases.append({"case_id": f"a3_{qi + 1:02d}", "query": {"topic": topic, "method": method,
                      "text": f"Find the most relevant studies that apply {method} to {topic}, and summarise "
                              f"which datasets they used and what results they report."},
                      "candidates": [{k: d[k] for k in ("doc_id", "title", "authors", "year", "abstract")} for d in cands],
                      "relevance": rel, "facts": {d["doc_id"]: d["facts"] for d in cands}})
    return cases
