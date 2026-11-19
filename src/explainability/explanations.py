"""Deterministic template explanations rendered ONLY from a DecisionTrace.

Every sentence of an explanation is a *claim*: a fixed template (by kind) filled with parameters,
each parameter bound to a field of the trace (a path into ``trace.model_dump(mode="json")``).
Parameters that are not plain field copies (e.g. "stay"/"switch") are derived from bound fields and
re-derived by the faithfulness checker (src.explainability.validation). No text is invented: the
explanation is the newline-joined claim texts, in order.

Binding path segments: dict key (str) | list index (int) | {"path_id": X} list selector |
"#len" (length) | "#part:i" (i-th model of a path id). A path starting with "#stage", i resolves to
the i-th canonical stage name.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.contracts import STAGES, DecisionTrace, Strategy, canonical_json, parse_path_id, sha256_hex
from src.routing.counterfactual import alternatives_for
from src.routing.scoring import fmt

TEMPLATES: dict[str, str] = {
    "header": "Strategy {strategy} decided for project {target}; training projects: {training}.",
    "oracle_note": "This is a retrospective oracle computed from observed outcomes of {target}; it is not a deployable router.",
    "policy": "Fixed single-model baseline policy: {policy}.",
    "predictor": "Predictor: {predictor}.",
    "selected": "Selected path {path}.",
    "no_feasible": "No feasible path: no candidate satisfied the feasibility threshold and the quality constraints.",
    "step": "Step {order} ({rule}): {detail}; removed {n_removed}, {n_remaining} remain.",
    "step_inactive": "Step {order} ({rule}) INACTIVE: {reason}.",
    "inactive_criteria": "Inactive criteria (skipped, not treated as 0): {criteria}.",
    "stage_model": "Stage {stage}: model {model}.",
    "transition": "Transition {from_stage} -> {to_stage}: {kind} ({from_model} -> {to_model}).",
    "n_switches": "The selected path has {n} model switch(es).",
    "swap_removed": "Alternative {alt} ({alt_model} at {stage}) was removed at step {order} ({rule}): {reason}.",
    "swap_missing": "Alternative {alt} ({alt_model} at {stage}) has no prediction (not a candidate of this strategy).",
    "decisive": "Decisive step: step {order} ({rule}) removed the last competing paths.",
    "uncertainty": "Selected path predicted {quantity} = {value} (range {lo} to {hi}).",
    "uncertainty_point": "Selected path predicted {quantity} = {value} (no range available).",
    "interaction": ("Interaction term for {quantity} on the selected path: {value} (observed training path outcome "
                    "minus stage-additive prediction, shrunk; not a causal handoff cost)."),
    "wwc_flip": ("What would change: if {parameter} ({quantity} {op}) moved from {current} to {flip} ({direction}), "
                 "the router would select {new}."),
    "wwc_flip_none": ("What would change: if {parameter} ({quantity} {op}) moved from {current} to {flip} "
                      "({direction}), the router would return no feasible path."),
    "wwc_none": ("What would change: no single change of {parameter} ({quantity} {op}) across the candidates' "
                 "predicted values changes the selection."),
}


def fmt_param(v: Any) -> str:
    if isinstance(v, list):
        return ", ".join(fmt_param(x) for x in v) if v else "none"
    return fmt(v)


def render_text(kind: str, params: dict) -> str:
    return TEMPLATES[kind].format(**{k: fmt_param(v) for k, v in params.items()})


class Unresolvable(Exception):
    pass


def resolve(doc: dict, path: list) -> Any:
    if path and path[0] == "#stage":
        return STAGES[path[1]].value
    cur: Any = doc
    for seg in path:
        try:
            if isinstance(seg, dict):
                (k, v), = seg.items()
                cur = next(x for x in cur if x.get(k) == v)
            elif seg == "#len":
                cur = len(cur)
            elif isinstance(seg, str) and seg.startswith("#part:"):
                cur = parse_path_id(cur)[int(seg.split(":")[1])]
            elif isinstance(cur, list):
                cur = cur[seg]
            else:
                cur = cur[seg]
        except (KeyError, IndexError, TypeError, StopIteration, ValueError) as exc:
            raise Unresolvable(f"cannot resolve {path_str(path)} at {seg!r}") from exc
    return cur


def path_str(path: list) -> str:
    out = []
    for s in path:
        out.append(f"[path_id={s['path_id']}]" if isinstance(s, dict) else str(s))
    return "/".join(out)


@dataclass
class Explanation:
    trace_id: str
    trace_hash: str
    claims: list[dict]
    text: str
    kind: str = "template"

    @property
    def explanation_hash(self) -> str:
        return sha256_hex(self.text)

    def to_dict(self) -> dict:
        return {"trace_id": self.trace_id, "trace_hash": self.trace_hash, "kind": self.kind,
                "explanation_hash": self.explanation_hash, "text": self.text, "claims": self.claims}


@dataclass
class _Builder:
    doc: dict
    claims: list[dict] = field(default_factory=list)

    def add(self, kind: str, bindings: dict[str, list], derived: dict | None = None):
        params = {k: resolve(self.doc, p) for k, p in bindings.items()}
        params.update(derived or {})
        self.claims.append({"claim_id": f"c{len(self.claims)}", "kind": kind, "params": params,
                            "bindings": bindings, "derived": sorted((derived or {}).keys()),
                            "text": render_text(kind, params)})


UNCERTAINTY_FIELDS = {"feasible": "feasibility_prob", "end_to_end_ms": "end_to_end_ms",
                      "total_tokens": "total_tokens", "cost_usd": "cost_usd"}


def candidate_field(quantity: str) -> list:
    """Path inside a candidate for a quantity key."""
    if quantity in UNCERTAINTY_FIELDS:
        return [UNCERTAINTY_FIELDS[quantity]]
    return ["quality", quantity]


def render_explanation(trace: DecisionTrace) -> Explanation:
    doc = trace.model_dump(mode="json")
    b = _Builder(doc)
    b.add("header", {"strategy": ["strategy"], "target": ["target_project"], "training": ["training_projects"]})
    comps = doc["explanation_components"]
    if trace.strategy == Strategy.S4_ORACLE:
        b.add("oracle_note", {"target": ["target_project"]})
    if "policy_path_id" in comps:
        b.add("policy", {"policy": ["explanation_components", "policy_path_id"]})
    if "predictor" in comps:
        b.add("predictor", {"predictor": ["explanation_components", "predictor"]})
    if trace.selected_path_id is None:
        b.add("no_feasible", {})
    else:
        b.add("selected", {"path": ["selected_path_id"]})

    for i, st in enumerate(trace.selection_steps):
        base = ["selection_steps", i]
        if st.inactive:
            b.add("step_inactive", {"order": base + ["order"], "rule": base + ["rule"],
                                    "reason": base + ["inactive_reason"]})
        else:
            b.add("step", {"order": base + ["order"], "rule": base + ["rule"], "detail": base + ["detail"],
                           "n_removed": base + ["removed", "#len"], "n_remaining": base + ["remaining", "#len"]})
    if trace.inactive_criteria:
        b.add("inactive_criteria", {"criteria": ["inactive_criteria"]})

    sel = trace.selected_path_id
    if sel is not None:
        n = len(parse_path_id(sel))
        for i in range(n):
            b.add("stage_model", {"stage": ["#stage", i], "model": ["selected_path_id", f"#part:{i}"]})
        for i in range(n - 1):
            m = parse_path_id(sel)
            b.add("transition", {"from_stage": ["#stage", i], "to_stage": ["#stage", i + 1],
                                 "from_model": ["selected_path_id", f"#part:{i}"],
                                 "to_model": ["selected_path_id", f"#part:{i + 1}"]},
                  {"kind": "stay" if m[i] == m[i + 1] else "switch"})
        b.add("n_switches", {"n": ["candidates", {"path_id": sel}, "n_switches"]})

        # Why each stage's model: where every single-stage swap was eliminated.
        aliases = sorted({a for c in trace.candidates for a in parse_path_id(c.path_id)})
        cand_ids = {c.path_id for c in trace.candidates}
        sel_m = parse_path_id(sel)
        for alt in alternatives_for(sel, aliases):
            alt_m = parse_path_id(alt)
            diff = [i for i in range(n) if alt_m[i] != sel_m[i]]
            if len(diff) != 1:
                continue                                    # baselines differing at >1 stage: covered by counterfactuals
            i = diff[0]
            derived = {"alt": alt, "alt_model": alt_m[i]}
            if alt not in cand_ids:
                b.add("swap_missing", {"stage": ["#stage", i]}, derived)
                continue
            k = next(s.order for s in trace.selection_steps if alt in s.removed)
            b.add("swap_removed", {"stage": ["#stage", i], "order": ["selection_steps", k, "order"],
                                   "rule": ["selection_steps", k, "rule"],
                                   "reason": ["selection_steps", k, "removed", alt]}, derived)
        dec = [s.order for s in trace.selection_steps if s.removed]
        if dec:
            k = max(dec)
            b.add("decisive", {"order": ["selection_steps", k, "order"], "rule": ["selection_steps", k, "rule"]})

        # Uncertainty for the quantities the objective uses.
        cand = next(c for c in trace.candidates if c.path_id == sel)
        qkeys = ["feasible"] + [qc.key for qc in trace.objective.quality_constraints] + \
                [k for k in trace.objective.preference_order if k in UNCERTAINTY_FIELDS]
        for q in qkeys:
            cpath = ["candidates", {"path_id": sel}] + candidate_field(q)
            try:
                resolve(doc, cpath)
            except Unresolvable:
                continue
            if q in cand.uncertainty:
                upath = ["candidates", {"path_id": sel}, "uncertainty", q]
                b.add("uncertainty", {"value": cpath, "lo": upath + [0], "hi": upath + [1]}, {"quantity": q})
            else:
                b.add("uncertainty_point", {"value": cpath}, {"quantity": q})
        for q in sorted(cand.interaction_terms):
            b.add("interaction", {"value": ["candidates", {"path_id": sel}, "interaction_terms", q]}, {"quantity": q})

    for i, w in enumerate(comps.get("what_would_change", [])):
        base = ["explanation_components", "what_would_change", i]
        common = {"parameter": base + ["parameter"], "quantity": base + ["quantity"], "op": base + ["op"]}
        if not w["flips"]:
            b.add("wwc_none", common)
        elif w["new_selected"] is None:
            b.add("wwc_flip_none", {**common, "current": base + ["current"], "flip": base + ["flip_threshold"],
                                    "direction": base + ["direction"]})
        else:
            b.add("wwc_flip", {**common, "current": base + ["current"], "flip": base + ["flip_threshold"],
                               "direction": base + ["direction"], "new": base + ["new_selected"]})

    text = "\n".join(c["text"] for c in b.claims)
    return Explanation(trace_id=trace.trace_id, trace_hash=trace.trace_hash(), claims=b.claims, text=text)


def explanation_digest(expl: Explanation) -> str:
    return sha256_hex(canonical_json(expl.to_dict()))
