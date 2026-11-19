"""Offline, rule-based model selection for the tier-matched v2.2 protocol.

Only the two saved AWS Price List snapshots and the saved Bedrock discovery
record are inputs.  This module never creates an AWS client or uses the network.
Access probes are deliberately represented as pending at CP3.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
PRICING_DIR = REPO / "results/raw/pricing"
DISCOVERY = REPO / "results/raw/model_discovery_2026-11-18.json"
OUT = REPO / "results/processed/independent_v2/tier_matched_selection.json"
TARGET_PROVIDERS = ("Amazon", "Anthropic", "OpenAI")
TIERS = {"low": (None, 1.50), "high": (3.00, 10.00)}
RETRIEVED = "2026-11-18"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _price_url(snapshot: dict[str, Any]) -> str:
    return (
        "https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/"
        f"{snapshot['offerCode']}/{snapshot['version']}/us-east-1/index.json"
    )


def _per_million(snapshot: dict[str, Any], sku: str) -> float:
    terms = snapshot["terms"]["OnDemand"].get(sku, {})
    dimensions = [
        dimension
        for term in terms.values()
        for dimension in term.get("priceDimensions", {}).values()
    ]
    if len(dimensions) != 1:
        raise ValueError(f"{sku}: expected exactly one on-demand price dimension")
    dimension = dimensions[0]
    value = float(dimension["pricePerUnit"]["USD"])
    unit = dimension["unit"].casefold()
    if unit == "1m tokens":
        return value
    if unit == "1k tokens":
        return value * 1000
    raise ValueError(f"{sku}: unsupported token unit {dimension['unit']!r}")


def _provider(attributes: dict[str, str]) -> str | None:
    if attributes.get("provider") in {"Anthropic", "OpenAI"}:
        return attributes["provider"]
    if attributes.get("model", "").casefold().startswith("nova"):
        return "Amazon"
    return None


def _model_key(provider: str, name: str) -> str:
    text = name.casefold()
    for prefix in ("amazon ", "anthropic ", "openai "):
        if text.startswith(prefix):
            text = text[len(prefix):]
    text = re.sub(r"\b(\d+)\.0\b", r"\1", text)
    return re.sub(r"[^a-z0-9]+", "", text)


def _is_standard_regional_token_sku(attributes: dict[str, str]) -> bool:
    if attributes.get("regionCode") != "us-east-1":
        return False
    if attributes.get("feature", "").casefold() != "on-demand inference":
        return False
    if attributes.get("inferenceType", "").casefold() not in {"input tokens", "output tokens"}:
        return False
    joined = " ".join(
        str(attributes.get(key, ""))
        for key in ("usagetype", "inferenceType", "feature", "service_tier")
    ).casefold()
    excluded = (
        "global", "batch", "cache", "priority", "flex", "latency", "custom",
        "provisioned", "long_ctx", "mantle",
    )
    return not any(marker in joined for marker in excluded)


def read_prices() -> tuple[dict[tuple[str, str], dict[str, Any]], list[dict[str, Any]]]:
    observations: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    sources = []
    for path in sorted(PRICING_DIR.glob("*.json")):
        snapshot = json.loads(path.read_text())
        sources.append({
            "path": str(path.relative_to(REPO)),
            "sha256": sha256(path),
            "offer_code": snapshot["offerCode"],
            "version": snapshot["version"],
            "publication_date": snapshot["publicationDate"],
            "source_url": _price_url(snapshot),
            "retrieved": RETRIEVED,
        })
        for sku, product in snapshot["products"].items():
            attributes = product.get("attributes", {})
            provider = _provider(attributes)
            if provider not in TARGET_PROVIDERS or not _is_standard_regional_token_sku(attributes):
                continue
            direction = "input" if attributes["inferenceType"].casefold() == "input tokens" else "output"
            model_name = attributes["model"]
            observations[(provider, _model_key(provider, model_name), direction)].append({
                "price_per_mtok": _per_million(snapshot, sku),
                "sku": sku,
                "snapshot": str(path.relative_to(REPO)),
                "pricing_model_name": model_name,
                "usage_type": attributes.get("usagetype"),
            })

    prices: dict[tuple[str, str], dict[str, Any]] = {}
    pairs = {(provider, key) for provider, key, _ in observations}
    for pair in sorted(pairs):
        entry: dict[str, Any] = {"observations": {}}
        for direction in ("input", "output"):
            seen = observations.get((*pair, direction), [])
            entry["observations"][direction] = seen
            values = sorted({row["price_per_mtok"] for row in seen})
            entry[f"{direction}_per_mtok"] = values[0] if len(values) == 1 else None
            if len(values) > 1:
                entry.setdefault("price_errors", []).append(f"ambiguous_{direction}_prices:{values}")
            elif not values:
                entry.setdefault("price_errors", []).append(f"missing_{direction}_price")
        if entry["input_per_mtok"] is not None and entry["output_per_mtok"] is not None:
            entry["blended_per_mtok"] = (
                3 * entry["input_per_mtok"] + entry["output_per_mtok"]
            ) / 4
        else:
            entry["blended_per_mtok"] = None
        prices[pair] = entry
    return prices, sources


def _version_key(provider: str, model_name: str, model_id: str) -> list[int]:
    text = f"{model_name} {model_id}".casefold()
    if provider == "OpenAI" and "gpt-oss" in text:
        return [0, 0, 0]
    if provider == "Amazon":
        match = re.search(r"\bnova\s*[- ]?(\d+(?:\.\d+)?)", text)
        parts = [int(part) for part in match.group(1).split(".")] if match else [1, 0]
        return (parts + [0, 0, 0])[:3]
    if provider == "Anthropic":
        match = re.search(r"claude\D+(\d+(?:\.\d+)?)", text)
    else:
        match = re.search(r"gpt[- ]?(\d+(?:\.\d+)?)", text)
    parts = [int(part) for part in match.group(1).split(".")] if match else [0]
    return (parts + [0, 0, 0])[:3]


def _tier(blended: float | None) -> str | None:
    if blended is None:
        return None
    if blended <= 1.50:
        return "low"
    if 3.00 <= blended <= 10.00:
        return "high"
    return None


def _us_profile(profiles: list[dict[str, Any]], base_model_id: str) -> str | None:
    matches = []
    for profile in profiles:
        if not profile.get("profile_id", "").startswith("us.") or profile.get("status") != "ACTIVE":
            continue
        if any(
            model.get("model_id") == base_model_id and model.get("region") == "us-east-1"
            for model in profile.get("models", [])
        ):
            matches.append(profile["profile_id"])
    return sorted(matches)[0] if matches else None


def build_selection() -> dict[str, Any]:
    price_map, price_sources = read_prices()
    discovery = json.loads(DISCOVERY.read_text())
    discovery_rows: dict[tuple[str, str], dict[str, Any]] = {}
    for model in discovery["text_models"]:
        provider = model.get("provider")
        if provider not in TARGET_PROVIDERS:
            continue
        key = (provider, _model_key(provider, model["model_name"]))
        if key in discovery_rows:
            # Provisioned-only variants share a display name. Prefer a base entry that is
            # on-demand/profile callable, then the lexically shortest ID.
            old = discovery_rows[key]
            old_score = (bool(set(old["inference_types"]) & {"ON_DEMAND", "INFERENCE_PROFILE"}), -len(old["model_id"]))
            new_score = (bool(set(model["inference_types"]) & {"ON_DEMAND", "INFERENCE_PROFILE"}), -len(model["model_id"]))
            if new_score <= old_score:
                continue
        discovery_rows[key] = model

    profiles = discovery["system_inference_profiles"]
    candidate_keys = sorted(set(discovery_rows) | set(price_map))
    candidates = []
    for provider, key in candidate_keys:
        found = discovery_rows.get((provider, key))
        priced = price_map.get((provider, key))
        reasons = []
        base_id = found.get("model_id") if found else None
        profile_id = _us_profile(profiles, base_id) if base_id else None
        inference_types = found.get("inference_types", []) if found else []
        callable_id = base_id if "ON_DEMAND" in inference_types else profile_id
        name = found.get("model_name") if found else next(
            row["pricing_model_name"]
            for direction in ("input", "output")
            for row in priced["observations"].get(direction, [])
        )
        input_price = priced.get("input_per_mtok") if priced else None
        output_price = priced.get("output_per_mtok") if priced else None
        blended = priced.get("blended_per_mtok") if priced else None
        band = _tier(blended)
        lower_name = name.casefold()

        if found is None:
            reasons.append("not_in_discovery")
        else:
            if found.get("lifecycle_status") != "ACTIVE":
                reasons.append(f"lifecycle_{str(found.get('lifecycle_status')).lower()}")
            if "TEXT" not in found.get("input_modalities", []) or "TEXT" not in found.get("output_modalities", []):
                reasons.append("not_text_in_text_out")
            if callable_id is None:
                reasons.append("no_on_demand_or_active_us_profile")
        if priced is None:
            reasons.append("not_in_pricing_snapshots")
        elif priced.get("price_errors"):
            reasons.extend(priced["price_errors"])
        if "safeguard" in lower_name:
            reasons.append("safeguard_variant")
        if "sonic" in lower_name or "speech" in lower_name:
            reasons.append("speech_variant")
        if blended is not None and band is None:
            reasons.append("outside_tier_bands")

        offline_eligible = not reasons and band is not None
        candidates.append({
            "provider": provider,
            "model_name": name,
            "base_model_id": base_id,
            "callable_model_id": callable_id,
            "version_key": _version_key(provider, name, base_id or ""),
            "lifecycle_status": found.get("lifecycle_status") if found else None,
            "inference_types": inference_types,
            "input_per_mtok": input_price,
            "output_per_mtok": output_price,
            "blended_per_mtok": blended,
            "band": band,
            "offline_eligible": offline_eligible,
            "access_probe_status": "not_run",
            "eligibility": "eligible_pending_access_probe" if offline_eligible else "ineligible",
            "reason": "access_probe_required" if offline_eligible else ";".join(reasons),
            "price_observations": priced.get("observations") if priced else None,
        })

    slots = []
    for provider in TARGET_PROVIDERS:
        for band in TIERS:
            eligible = [
                row for row in candidates
                if row["provider"] == provider and row["band"] == band and row["offline_eligible"]
            ]
            selected = sorted(
                eligible,
                key=lambda row: (
                    tuple(-part for part in row["version_key"]),
                    row["blended_per_mtok"],
                    row["base_model_id"],
                ),
            )[0] if eligible else None
            slots.append({
                "provider": provider,
                "band": band,
                "status": "selected_pending_access_probe" if selected else "empty_no_offline_eligible_model",
                "base_model_id": selected["base_model_id"] if selected else None,
                "callable_model_id": selected["callable_model_id"] if selected else None,
            })

    return {
        "protocol": "tier-matched-v2.2",
        "status": "cp3_selection_pending_access_probes",
        "generated_offline": True,
        "selection_rule": {
            "blended_formula": "(3 * input_per_mtok + output_per_mtok) / 4",
            "bands": {"low": "<= 1.50", "high": "3.00 <= price <= 10.00"},
            "newest": "highest parsed vendor version; ties lower blended price, then base model ID",
            "access_probe_required_for_final_eligibility": True,
            "near_miss_substitution": False,
        },
        "inputs": {
            "discovery": {
                "path": str(DISCOVERY.relative_to(REPO)),
                "sha256": sha256(DISCOVERY),
            },
            "pricing_snapshots": price_sources,
        },
        "selected_slots": slots,
        "candidates": candidates,
    }


def markdown_table(result: dict[str, Any]) -> str:
    lines = [
        "| Vendor | Model | Input $/M | Output $/M | Blended $/M | Band | Eligibility | Reason |",
        "|---|---|---:|---:|---:|---|---|---|",
    ]
    for row in result["candidates"]:
        value = lambda key: "—" if row[key] is None else f"{row[key]:.4f}"  # noqa: E731
        lines.append(
            f"| {row['provider']} | `{row['base_model_id'] or row['model_name']}` | "
            f"{value('input_per_mtok')} | {value('output_per_mtok')} | {value('blended_per_mtok')} | "
            f"{row['band'] or '—'} | {row['eligibility']} | {row['reason']} |"
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify committed output without writing")
    parser.add_argument("--markdown", action="store_true", help="print the full candidate table")
    args = parser.parse_args(argv)
    result = build_selection()
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.check:
        if not OUT.exists() or OUT.read_text() != payload:
            raise SystemExit("tier-matched selection output is missing or stale")
    else:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(payload)
    print(markdown_table(result) if args.markdown else json.dumps(result["selected_slots"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
