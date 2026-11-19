"""Counterfactual predictions and the append-only, hash-chained prediction log.

For a prospective trace with a selected path, alternatives are:
  * every single-stage swap (replace the model at one stage by each other model), and
  * every single-model baseline (X-X-X) other than the selected path.
Predicted values are taken from the trace's own candidate predictions (same strategy, same
training data), so the counterfactual is exactly what the router believed when it decided.

Delta = alternative - selected. Delta interval (conservative, ignores correlation):
  [alt_lo - sel_hi, alt_hi - sel_lo]; n_switches is deterministic, so its interval is a point.

Log format (one JSON object per line):
  {"seq": i, "prev_hash": <chain hash of line i-1 | null>, "content_hash": <record content hash>,
   "chain_hash": chain_hash(prev_hash, content_hash), "record": {...}}
A sidecar "<log>.head" stores {"seq", "chain_hash"} of the last line so truncation of the tail is
detectable too. verify_chain() re-validates each record (for predictions: the contract recomputes
the canonical content hash) and every link.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from src.contracts import (
    CounterfactualPrediction,
    DecisionTrace,
    PathPrediction,
    canonical_json,
    chain_hash,
    make_path_id,
    parse_path_id,
    sha256_hex,
)
from src.contracts.routing import PROSPECTIVE

from .scoring import quantity

PREDICTED_KEYS_EFF = ("end_to_end_ms", "total_tokens", "cost_usd", "n_switches")


def alternatives_for(selected: str, aliases: list[str]) -> list[str]:
    models = list(parse_path_id(selected))
    alts: list[str] = []
    for i in range(len(models)):
        for m in aliases:
            if m != models[i]:
                alt = models.copy()
                alt[i] = m
                alts.append(make_path_id(alt))
    for m in aliases:
        b = make_path_id([m] * len(models))
        if b != selected and b not in alts:
            alts.append(b)
    return alts


def prediction_values(c: PathPrediction) -> dict[str, float | None]:
    v: dict[str, float | None] = {"feasible": c.feasibility_prob}
    v.update({k: c.quality[k] for k in sorted(c.quality)})
    for k in PREDICTED_KEYS_EFF:
        v[k] = quantity(c, k)
    return v


def _interval(c: PathPrediction, key: str, point: float | None):
    if point is None:
        return None
    if key == "n_switches":
        return (point, point)
    u = c.uncertainty.get(key)
    return tuple(u) if u is not None else (point, point)


def generate_counterfactuals(trace: DecisionTrace, created_at: str, aliases: list[str] | None = None
                             ) -> tuple[list[CounterfactualPrediction], list[str]]:
    """Returns (predictions, notes). Refuses non-prospective (oracle) traces."""
    if trace.strategy not in PROSPECTIVE:
        raise ValueError("counterfactual predictions are only made for prospective strategies (S1-S3), never S4")
    if trace.selected_path_id is None:
        return [], ["no feasible path selected; no counterfactuals generated"]
    by_id = {c.path_id: c for c in trace.candidates}
    aliases = aliases or sorted({m for c in trace.candidates for m in parse_path_id(c.path_id)})
    sel = by_id[trace.selected_path_id]
    sv = prediction_values(sel)
    preds, notes = [], []
    for alt in alternatives_for(trace.selected_path_id, aliases):
        if alt not in by_id:
            notes.append(f"{alt}: not among this trace's candidates (strategy {trace.strategy.value}); skipped")
            continue
        a = by_id[alt]
        av = prediction_values(a)
        keys = sorted(set(sv) | set(av))
        delta = {k: (av.get(k) - sv.get(k)) if av.get(k) is not None and sv.get(k) is not None else None
                 for k in keys}
        dint = {}
        for k in keys:
            ia, is_ = _interval(a, k, av.get(k)), _interval(sel, k, sv.get(k))
            dint[k] = None if ia is None or is_ is None else (ia[0] - is_[1], ia[1] - is_[0])
        preds.append(CounterfactualPrediction.create(
            prediction_id=f"{trace.trace_id}::{alt}", trace_id=trace.trace_id, created_at=created_at,
            strategy=trace.strategy, router_version=trace.router_version, config_hash=trace.config_hash,
            objective_id=trace.objective.objective_id, held_out_project=trace.held_out_project,
            training_projects=trace.training_projects, training_data_hash=trace.training_data_hash,
            selected_path_id=trace.selected_path_id, alternative_path_id=alt,
            predicted_selected={k: sv.get(k) for k in keys}, predicted_alternative={k: av.get(k) for k in keys},
            predicted_delta=delta, predicted_delta_interval=dint,
        ))
    return preds, notes


# ----------------------------------------------------------------------------- hash-chained log
def _prediction_hash(rec: dict) -> str:
    return CounterfactualPrediction.model_validate(rec).content_hash   # raises if content was edited


def generic_hash(rec: dict) -> str:
    return sha256_hex(canonical_json(rec))


@dataclass
class ChainReport:
    ok: bool
    n_lines: int
    errors: list[str] = field(default_factory=list)
    head: str | None = None


class HashChainLog:
    """Append-only JSONL log with a hash chain. Never rewrites existing lines."""

    def __init__(self, path: str | Path, content_hash: Callable[[dict], str] = generic_hash):
        self.path = Path(path)
        self.head_path = self.path.with_name(self.path.name + ".head")
        self.content_hash = content_hash

    def verify(self) -> ChainReport:
        return verify_chain(self.path, self.content_hash)

    def records(self) -> list[dict]:
        rep = self.verify()
        if not rep.ok:
            raise ValueError(f"hash chain broken in {self.path}: {rep.errors}")
        if not self.path.exists():
            return []
        return [json.loads(line)["record"] for line in self.path.read_text().splitlines() if line.strip()]

    def append(self, record: dict) -> str:
        rep = self.verify()
        if not rep.ok:
            raise ValueError(f"refusing to append: hash chain broken in {self.path}: {rep.errors}")
        prev, seq = rep.head, rep.n_lines
        ch = self.content_hash(record)
        link = chain_hash(prev, ch)
        line = {"seq": seq, "prev_hash": prev, "content_hash": ch, "chain_hash": link, "record": record}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "a") as fh:
            fh.write(canonical_json(line) + "\n")
        self.head_path.write_text(canonical_json({"seq": seq, "chain_hash": link}) + "\n")
        return link


def verify_chain(path: str | Path, content_hash: Callable[[dict], str] = generic_hash) -> ChainReport:
    path = Path(path)
    head_path = path.with_name(path.name + ".head")
    if not path.exists():
        if head_path.exists():
            return ChainReport(False, 0, ["log file missing but head file exists (log deleted?)"])
        return ChainReport(True, 0, [], None)
    errors: list[str] = []
    prev = None
    n = 0
    for i, raw in enumerate([ln for ln in path.read_text().splitlines() if ln.strip()]):
        n += 1
        try:
            line = json.loads(raw)
        except json.JSONDecodeError:
            errors.append(f"line {i}: not valid JSON")
            prev = None
            continue
        if line.get("seq") != i:
            errors.append(f"line {i}: seq {line.get('seq')} != {i} (deleted or reordered line)")
        if line.get("prev_hash") != prev:
            errors.append(f"line {i}: prev_hash does not link to the previous line (deleted or reordered line)")
        try:
            ch = content_hash(line.get("record"))
        except Exception as exc:  # noqa: BLE001
            errors.append(f"line {i}: record fails validation ({exc.__class__.__name__}): edited content")
            ch = None
        if ch is not None and ch != line.get("content_hash"):
            errors.append(f"line {i}: content hash mismatch (edited record)")
        if line.get("chain_hash") != chain_hash(line.get("prev_hash"), line.get("content_hash") or ""):
            errors.append(f"line {i}: chain_hash mismatch")
        prev = line.get("chain_hash")
    if head_path.exists():
        head = json.loads(head_path.read_text())
        if head.get("seq") != n - 1 or head.get("chain_hash") != prev:
            errors.append(f"head file says seq={head.get('seq')} hash={str(head.get('chain_hash'))[:12]}, "
                          f"log ends at seq={n - 1} (truncated or extended outside the API)")
    elif n:
        errors.append("head file missing")
    return ChainReport(not errors, n, errors, prev)


class PredictionLog(HashChainLog):
    """Hash-chained log of CounterfactualPrediction records (content hash = the contract's content_hash)."""

    def __init__(self, path: str | Path):
        super().__init__(path, _prediction_hash)

    def append_prediction(self, pred: CounterfactualPrediction) -> str:
        if pred.content_hash != pred.computed_hash():
            raise ValueError("refusing to log a prediction whose content hash does not match")
        return self.append(pred.model_dump(mode="json"))

    def predictions(self) -> list[CounterfactualPrediction]:
        return [CounterfactualPrediction.model_validate(r) for r in self.records()]
