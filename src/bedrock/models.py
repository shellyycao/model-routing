"""Model registry: typed model specs loaded from configs/models.yaml."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import yaml
from pydantic import BaseModel, Field, model_validator

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODELS_CONFIG = REPO_ROOT / "configs" / "models.yaml"


class PricingConfigError(ValueError):
    """A manually entered price is incomplete or lacks provenance."""


class Pricing(BaseModel):
    """USD per 1M tokens. None means the price has not been verified."""

    input_per_mtok: float | None = None
    output_per_mtok: float | None = None
    source: str | None = None
    retrieved: str | None = None

    @property
    def verified(self) -> bool:
        """Both prices set AND provenance recorded (non-empty source, ISO `retrieved` date)."""
        if self.input_per_mtok is None or self.output_per_mtok is None:
            return False
        try:
            self.validate_manual()
        except PricingConfigError:
            return False
        return True

    def validate_manual(self, alias: str = "?") -> None:
        """Rules for prices loaded from config (see configs/models.yaml):
        - both prices null (unverified), or both set and >= 0;
        - a set price must carry a non-empty `source` and a `retrieved` ISO date (YYYY-MM-DD).
        """
        prices = (self.input_per_mtok, self.output_per_mtok)
        if all(p is None for p in prices):
            return
        if any(p is None for p in prices):
            raise PricingConfigError(
                f"Model {alias}: set both input_per_mtok and output_per_mtok, or leave both null")
        if any(p < 0 for p in prices):
            raise PricingConfigError(f"Model {alias}: prices must be >= 0")
        if not (self.source or "").strip():
            raise PricingConfigError(f"Model {alias}: a price requires a non-empty `source`")
        try:
            date.fromisoformat(str(self.retrieved))
        except (TypeError, ValueError):
            raise PricingConfigError(
                f"Model {alias}: a price requires `retrieved` as an ISO date (YYYY-MM-DD), "
                f"got {self.retrieved!r}") from None


class InferenceSettings(BaseModel):
    max_tokens: int = 4096
    temperature: float | None = 0.0


class RateLimitSettings(BaseModel):
    """Self-imposed client-side pacing for one model (not an AWS quota)."""

    min_interval_s: float = Field(default=0.0, ge=0)
    requests_per_minute: float | None = Field(default=None, gt=0)

    @property
    def interval_s(self) -> float:
        """Effective minimum spacing between request starts (the stricter of the two)."""
        rpm_interval = 60.0 / self.requests_per_minute if self.requests_per_minute else 0.0
        return max(self.min_interval_s, rpm_interval)


class ConcurrencySettings(BaseModel):
    max_workers: int = Field(default=1, ge=1)
    default: RateLimitSettings = Field(default_factory=RateLimitSettings)
    per_model: dict[str, RateLimitSettings] = Field(default_factory=dict)

    def for_model(self, alias: str) -> RateLimitSettings:
        return self.per_model.get(alias, self.default)


class ModelSpec(BaseModel):
    alias: str
    name: str
    family: str
    model_id: str
    base_model_id: str
    notes: str | None = None
    pricing: Pricing = Field(default_factory=Pricing)
    inference: InferenceSettings = Field(default_factory=InferenceSettings)


class ModelRegistry(BaseModel):
    region: str
    aws_profile: str | None = None
    models: dict[str, ModelSpec]
    concurrency: ConcurrencySettings = Field(default_factory=ConcurrencySettings)

    @model_validator(mode="after")
    def _unique_ids(self) -> "ModelRegistry":
        # get() resolves by model_id and base_model_id, so both must be unambiguous.
        for field in ("model_id", "base_model_id"):
            seen: dict[str, str] = {}
            for alias, spec in self.models.items():
                v = getattr(spec, field)
                if v in seen:
                    raise ValueError(f"Duplicate {field} {v!r} for aliases {seen[v]} and {alias}")
                seen[v] = alias
        return self

    def get(self, alias_or_id: str) -> ModelSpec:
        if alias_or_id in self.models:
            return self.models[alias_or_id]
        for spec in self.models.values():
            if alias_or_id in (spec.model_id, spec.base_model_id):
                return spec
        raise KeyError(f"Unknown model {alias_or_id!r}; known: {sorted(self.models)}")

    @property
    def aliases(self) -> list[str]:
        return sorted(self.models)

    def pricing_status(self) -> dict:
        """Which models are priced, from what source and date. Unpriced models have
        cost recorded as `unavailable` (never $0) and keep the dollar guard inactive."""
        models = {
            alias: {
                "model_id": spec.model_id,
                "priced": spec.pricing.verified,
                "input_per_mtok": spec.pricing.input_per_mtok,
                "output_per_mtok": spec.pricing.output_per_mtok,
                "source": spec.pricing.source,
                "retrieved": spec.pricing.retrieved,
            }
            for alias, spec in sorted(self.models.items())
        }
        unpriced = [a for a, m in models.items() if not m["priced"]]
        return {
            "all_priced": not unpriced,
            "priced": [a for a, m in models.items() if m["priced"]],
            "unpriced": unpriced,
            "dollar_guard_possible": not unpriced,
            "models": models,
        }


def load_registry(path: str | Path = DEFAULT_MODELS_CONFIG) -> ModelRegistry:
    raw = yaml.safe_load(Path(path).read_text())
    default_inf = raw.get("default_inference", {})
    models = {}
    for alias, m in raw["models"].items():
        m = dict(m)
        inf = {**default_inf, **(m.pop("inference", None) or {})}
        spec = ModelSpec(alias=alias, inference=InferenceSettings(**inf), **m)
        spec.pricing.validate_manual(alias)
        models[alias] = spec
    concurrency = ConcurrencySettings(**(raw.get("concurrency") or {}))
    unknown = set(concurrency.per_model) - set(models)
    if unknown:
        raise ValueError(f"concurrency.per_model has unknown aliases: {sorted(unknown)}")
    return ModelRegistry(region=raw["region"], aws_profile=raw.get("aws_profile"),
                         models=models, concurrency=concurrency)
