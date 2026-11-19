"""Routing configuration (configs/routing.yaml) -> RoutingObjective + estimator settings."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from src.contracts import RoutingObjective, canonical_json, sha256_hex

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = REPO_ROOT / "configs" / "routing.yaml"


@dataclass(frozen=True)
class RouterSettings:
    """Settings the router needs besides the objective. Stored in every trace so it can be replayed."""

    pareto_quality_keys: tuple[str, ...] | str = "all"

    def to_dict(self) -> dict[str, Any]:
        q = self.pareto_quality_keys
        return {"pareto_quality_keys": q if isinstance(q, str) else list(q)}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "RouterSettings":
        q = d.get("pareto_quality_keys", "all")
        return cls(pareto_quality_keys=q if isinstance(q, str) else tuple(q))


@dataclass(frozen=True)
class RoutingConfig:
    router_version: str
    objective: RoutingObjective
    settings: RouterSettings
    interaction_shrinkage_k: float
    uncertainty: str
    raw: dict = field(repr=False)

    @property
    def config_hash(self) -> str:
        return sha256_hex(canonical_json(self.raw))


def config_from_dict(raw: dict) -> RoutingConfig:
    obj = RoutingObjective.model_validate(raw["objective"])
    pareto = raw.get("pareto", {}) or {}
    qk = pareto.get("quality_keys", "all")
    if not (qk == "all" or isinstance(qk, list)):
        raise ValueError("pareto.quality_keys must be 'all' or a list of '<stage>.<metric>' keys")
    est = raw.get("estimation", {}) or {}
    k = float(est.get("interaction_shrinkage_k", 2.0))
    if k < 0:
        raise ValueError("interaction_shrinkage_k must be >= 0")
    unc = est.get("uncertainty", "project_range")
    if unc != "project_range":
        raise ValueError(f"unsupported uncertainty method {unc!r} (only 'project_range' is implemented)")
    return RoutingConfig(
        router_version=str(raw.get("router_version", "0.0.0")),
        objective=obj,
        settings=RouterSettings(pareto_quality_keys=qk if isinstance(qk, str) else tuple(qk)),
        interaction_shrinkage_k=k,
        uncertainty=unc,
        raw=raw,
    )


def load_routing_config(path: str | Path = DEFAULT_CONFIG_PATH) -> RoutingConfig:
    with open(path) as fh:
        raw = yaml.safe_load(fh)
    return config_from_dict(raw)
