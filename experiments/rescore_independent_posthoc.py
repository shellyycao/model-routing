"""POST-HOC secondary scoring for the independent benchmarks (never replaces the frozen v1 scores).

1. A3 grounding v1.1: the frozen scorer compares topic/method claims with the CANONICAL fact label, while the
   abstracts (by design) use paraphrased surface forms and the prompt asks for values "exactly as stated in the
   abstract". v1.1 additionally accepts a topic/method claim whose value is, for EVERY cited document, one of the
   documented surface forms of that document's canonical fact (datasets/independent/a3_gen.py TOPIC_FORMS /
   METHOD_FORMS). A paraphrase of a DIFFERENT topic/method still fails.
   All other attributes are scored exactly as in v1.
2. A2 content diagnostic: for responses that failed ONLY because the JSON lacked the required {"fields": ...}
   wrapper, score the unwrapped object with the frozen A2 scorer. Schema compliance stays failed; this measures
   extraction content separately.
Reads saved artifacts only; writes results/processed/independent/posthoc.json.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from datasets.independent.a3_gen import METHOD_FORMS, TOPIC_FORMS
from src.independent.tasks import A2Response, A3Response, _claim_ok, score_a2

REPO = Path(__file__).resolve().parents[1]
FORMS = {"topic": TOPIC_FORMS, "method": METHOD_FORMS}


def claim_ok_v11(claim, facts) -> bool:
    if _claim_ok(claim, facts):
        return True
    if claim.attribute not in FORMS or not claim.cited_ids:
        return False
    v = str(claim.value).strip().casefold()
    for cid in claim.cited_ids:
        f = facts.get(cid)
        if f is None:
            return False
        forms = [s.casefold() for s in FORMS[claim.attribute].get(f[claim.attribute], [])]
        if v not in forms:
            return False
    return True


def main() -> int:
    out = {"mode": "post_hoc_secondary", "warning": "Secondary analysis; frozen v1 scores remain primary.",
           "a3_grounding_v1_1": [], "a2_unwrapped_content": []}
    for l in (REPO / "results/raw/independent/indepA3_lit_v1.jsonl").read_text().splitlines():
        r = json.loads(l)
        if not r["parse_ok"]:
            continue
        case = json.loads((REPO / f"datasets/independent/a3/cases/{r['case_id']}.json").read_text())
        resp = A3Response.model_validate_json((REPO / f"results/raw/runs/{r['run_id']}/parsed.json").read_text())
        n = len(resp.claims)
        out["a3_grounding_v1_1"].append({"run_id": r["run_id"], "model": r["model_alias"], "case_id": r["case_id"],
                                         "grounding_v1": r["scores"].get("grounding_accuracy"),
                                         "grounding_v1_1": sum(claim_ok_v11(c, case["facts"]) for c in resp.claims) / n if n else 0.0})
    for l in (REPO / "results/raw/independent/indepA2_extract_v1.jsonl").read_text().splitlines():
        r = json.loads(l)
        if r["parse_ok"] or "fields\n  Field required" not in (r["failure_detail"] or ""):
            continue
        case = json.loads((REPO / f"datasets/independent/a2/cases/{r['case_id']}.json").read_text())
        txt = (REPO / f"results/raw/runs/{r['run_id']}/response.txt").read_text()
        obj = json.loads(re.search(r"\{.*\}", txt, re.S).group(0))
        _, s, _ = score_a2(case, A2Response(fields=obj))
        out["a2_unwrapped_content"].append({"run_id": r["run_id"], "model": r["model_alias"], "case_id": r["case_id"],
                                            "f1": s["f1"], "all_fields_correct": s["all_fields_correct"],
                                            "hallucinated_fields": s["hallucinated_fields"]})
    dest = REPO / "results/processed/independent/posthoc.json"
    dest.write_text(json.dumps(out, indent=2) + "\n")
    import statistics as st
    for m in "ABC":
        g = [x for x in out["a3_grounding_v1_1"] if x["model"] == m]
        if g:
            print(f"A3 {m}: grounding v1 mean {st.mean(x['grounding_v1'] for x in g):.3f} -> v1.1 {st.mean(x['grounding_v1_1'] for x in g):.3f} (n={len(g)})")
    print("A2 unwrapped:", [(x["model"], x["case_id"], x["f1"]) for x in out["a2_unwrapped_content"]])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
