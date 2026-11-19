"""Control-plane model discovery (free API calls only) and study-model annotation.

Used by scripts/discover_models.py. Functions here take an already-built `bedrock`
control-plane client so they can be tested with fakes. Nothing here reads or stores
credentials; ARNs are reduced to model/profile IDs and any 12-digit account number
that slips into a string is redacted before anything is printed or written.
"""

from __future__ import annotations

import re
from typing import Any

from .models import ModelRegistry

_ACCOUNT_RE = re.compile(r"(?<!\d)\d{12}(?!\d)")


def redact(value: Any) -> Any:
    """Recursively replace 12-digit numbers (AWS account IDs) with a placeholder."""
    if isinstance(value, str):
        return _ACCOUNT_RE.sub("<redacted-account>", value)
    if isinstance(value, dict):
        return {k: redact(v) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v) for v in value]
    return value


def _id_from_arn(arn: str | None) -> str | None:
    if not arn:
        return None
    return arn.rsplit("/", 1)[-1]


def _region_from_arn(arn: str | None) -> str | None:
    parts = (arn or "").split(":")
    return parts[3] if len(parts) > 3 and parts[3] else None


def list_text_models(bedrock: Any) -> list[dict]:
    resp = bedrock.list_foundation_models(byOutputModality="TEXT")
    out = []
    for m in resp.get("modelSummaries", []):
        out.append({
            "model_id": m.get("modelId"),
            "model_name": m.get("modelName"),
            "provider": m.get("providerName"),
            "input_modalities": m.get("inputModalities", []),
            "output_modalities": m.get("outputModalities", []),
            "inference_types": m.get("inferenceTypesSupported", []),
            "lifecycle_status": (m.get("modelLifecycle") or {}).get("status"),
            "streaming": m.get("responseStreamingSupported"),
        })
    return sorted(out, key=lambda d: d["model_id"] or "")


def list_system_profiles(bedrock: Any) -> list[dict]:
    out, token = [], None
    while True:
        kw: dict[str, Any] = {"typeEquals": "SYSTEM_DEFINED", "maxResults": 1000}
        if token:
            kw["nextToken"] = token
        resp = bedrock.list_inference_profiles(**kw)
        for p in resp.get("inferenceProfileSummaries", []):
            # The profile ARN embeds the account ID: store only the profile ID.
            out.append({
                "profile_id": p.get("inferenceProfileId"),
                "profile_name": p.get("inferenceProfileName"),
                "status": p.get("status"),
                "type": p.get("type"),
                "models": sorted(
                    ({"model_id": _id_from_arn(m.get("modelArn")), "region": _region_from_arn(m.get("modelArn"))}
                     for m in p.get("models", [])),
                    key=lambda d: (d["region"] or "", d["model_id"] or ""),
                ),
            })
        token = resp.get("nextToken")
        if not token:
            break
    return sorted(out, key=lambda d: d["profile_id"] or "")


def annotate_study_models(registry: ModelRegistry, text_models: list[dict], profiles: list[dict]) -> dict:
    """For each configured model: is the configured ID present and ACTIVE, and callable
    the way it is configured (in-region ON_DEMAND, or via a system inference profile)?"""
    fm = {m["model_id"]: m for m in text_models}
    prof = {p["profile_id"]: p for p in profiles}
    out = {}
    for alias, spec in sorted(registry.models.items()):
        base = fm.get(spec.base_model_id)
        entry: dict[str, Any] = {
            "model_id": spec.model_id,
            "base_model_id": spec.base_model_id,
            "base_model_present": base is not None,
            "base_model_lifecycle": base["lifecycle_status"] if base else None,
            "base_model_inference_types": base["inference_types"] if base else [],
        }
        if spec.model_id in prof:
            p = prof[spec.model_id]
            in_region = [m for m in p["models"] if m["region"] == registry.region]
            entry.update({
                "id_kind": "system_inference_profile",
                "present": True,
                "status": p["status"],
                "profile_includes_base_model": any(m["model_id"] == spec.base_model_id for m in p["models"]),
                "profile_includes_configured_region": any(
                    m["model_id"] == spec.base_model_id for m in in_region),
                "profile_regions": sorted({m["region"] for m in p["models"] if m["region"]}),
            })
            entry["active"] = (p["status"] == "ACTIVE" and entry["base_model_lifecycle"] == "ACTIVE")
            entry["callable_as_configured"] = entry["active"] and entry["profile_includes_base_model"]
        elif spec.model_id in fm:
            m = fm[spec.model_id]
            entry.update({
                "id_kind": "foundation_model",
                "present": True,
                "status": m["lifecycle_status"],
                "active": m["lifecycle_status"] == "ACTIVE",
            })
            entry["callable_as_configured"] = entry["active"] and "ON_DEMAND" in m["inference_types"]
        else:
            entry.update({"id_kind": "not_found", "present": False, "status": None,
                          "active": False, "callable_as_configured": False})
        out[alias] = entry
    return out


def build_report(registry: ModelRegistry, bedrock: Any, *, generated_at: str) -> dict:
    text_models = list_text_models(bedrock)
    profiles = list_system_profiles(bedrock)
    study = annotate_study_models(registry, text_models, profiles)
    report = {
        "generated_at": generated_at,
        "region": registry.region,
        "source": "bedrock control plane: ListFoundationModels(byOutputModality=TEXT), "
                  "ListInferenceProfiles(typeEquals=SYSTEM_DEFINED)",
        "note": "Control-plane metadata only; no inference was performed unless `probe` is present. "
                "Presence/ACTIVE status does not imply account access was granted for inference.",
        "counts": {
            "text_models": len(text_models),
            "text_models_active": sum(m["lifecycle_status"] == "ACTIVE" for m in text_models),
            "system_inference_profiles": len(profiles),
        },
        "study_models": study,
        "all_study_models_ok": all(e["callable_as_configured"] for e in study.values()),
        "text_models": text_models,
        "system_inference_profiles": profiles,
    }
    return redact(report)
