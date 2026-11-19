"""Offline verification of the three final price-matched-v2 models.

Prices come only from saved AWS Price List snapshots.  Access eligibility requires
saved evidence from a real Converse invocation; the control-plane availability
snapshot is retained as secondary evidence because it incorrectly reported Grok
4.7 as available.  No AWS client or network operation is created here.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
PRICING_DIR = REPO / "results/raw/pricing"
ACCESS = REPO / "results/raw/model_access_2026-11-18.json"
MODEL_PROBE = REPO / "results/raw/model_probe_2026-11-18.json"
PILOT_RECORDS = REPO / "results/raw/price_matched_v2_pilot/records.jsonl"
REPILOT_RECORDS = REPO / "results/raw/price_matched_v2_pilot/repilot_records.jsonl"
OUT = REPO / "results/processed/independent_v2/price_matched_model_verification.json"
RETRIEVED = "2026-11-18"
MODELS = (
    {
        "alias": "sonnet_4_6",
        "provider": "Anthropic",
        "pricing_model": "Claude Sonnet 4.6",
        "base_model_id": "anthropic.claude-sonnet-4-6",
        "callable_model_id": "us.anthropic.claude-sonnet-4-6",
        "expected_input_per_mtok": 3.30,
        "expected_output_per_mtok": 16.50,
    },
    {
        "alias": "kimi_k3",
        "provider": "Moonshot AI",
        "pricing_model": "Kimi K3",
        "base_model_id": "moonshotai.kimi-k3",
        "callable_model_id": "us.moonshotai.kimi-k3",
        "expected_input_per_mtok": 3.30,
        "expected_output_per_mtok": 16.50,
    },
    {
        "alias": "glm_5",
        "provider": "Z AI",
        "pricing_model": "GLM 5",
        "base_model_id": "zai.glm-5",
        "callable_model_id": "zai.glm-5",
        "expected_input_per_mtok": 1.00,
        "expected_output_per_mtok": 3.20,
    },
)

REMOVED_MODEL = {
    "alias": "grok_4_7",
    "base_model_id": "xai.grok-4.7",
    "callable_model_id": "us.xai.grok-4.7",
}


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
    dimensions = [
        dimension
        for term in snapshot["terms"]["OnDemand"].get(sku, {}).values()
        for dimension in term.get("priceDimensions", {}).values()
    ]
    if len(dimensions) != 1:
        raise ValueError(f"{sku}: expected one on-demand price dimension")
    unit = dimensions[0]["unit"].casefold()
    value = float(dimensions[0]["pricePerUnit"]["USD"])
    if unit == "1m tokens":
        return value
    if unit == "1k tokens":
        return value * 1000
    raise ValueError(f"{sku}: unsupported unit {dimensions[0]['unit']!r}")


def _regional_standard(attributes: dict[str, str]) -> bool:
    if attributes.get("regionCode") != "us-east-1":
        return False
    feature = attributes.get("feature")
    if feature is not None and feature.casefold() != "on-demand inference":
        return False
    if attributes.get("inferenceType", "").casefold() not in {"input tokens", "output tokens"}:
        return False
    combined = " ".join(
        str(attributes.get(key, ""))
        for key in ("usagetype", "inferenceType", "service_tier")
    ).casefold()
    # "mantle" is an AWS backend marker on valid regional standard Kimi/Grok SKUs.
    excluded = (
        "global", "batch", "cache", "priority", "flex", "latency", "custom",
        "provisioned", "long_ctx",
    )
    return not any(marker in combined for marker in excluded)


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _invoke_evidence(
    spec: dict[str, Any], pilot: list[dict[str, Any]], repilot: list[dict[str, Any]],
    probe: dict[str, Any],
) -> dict[str, Any]:
    repilot_rows = [row for row in repilot if row.get("model_id") == spec["callable_model_id"]]
    repilot_successes = [
        row for row in repilot_rows
        if row.get("status") == "success" and row.get("schema_parsed") is True
    ]
    if spec["alias"] == "glm_5":
        row = probe["results"]["glm_5"]
        success = row.get("status") == "success" and row.get("model_id") == spec["callable_model_id"]
        return {
            "sources": [
                str(MODEL_PROBE.relative_to(REPO)),
                str(REPILOT_RECORDS.relative_to(REPO)),
            ],
            "kind": "tiny_real_converse_probe_plus_structured_repilot",
            "status": row.get("status"),
            "model_id": row.get("model_id"),
            "stopReason": row.get("stopReason"),
            "usage": row.get("usage"),
            "repilot_successful_structured_calls": len(repilot_successes),
            "access_eligible": success and len(repilot_successes) == 3,
            "compatibility_verified": len(repilot_successes) == 3,
            "compatibility_status": "temperature_0_structured_output_verified_3_of_3",
        }

    rows = [row for row in pilot if row.get("model_id") == spec["callable_model_id"]]
    successes = [row for row in rows if row.get("status") == "success"]
    validation = [
        row for row in rows
        if (row.get("error") or {}).get("code") == "ValidationException"
    ]
    # A model-specific parameter ValidationException proves the invoke path reached
    # that model rather than failing account access. Compatibility is still pending.
    access_eligible = bool(successes or validation)
    compatibility_status = (
        "temperature_0_structured_output_verified"
        if successes
        else "temperature_rejected_no_temperature_repilot_required"
    )
    if spec["alias"] == "kimi_k3" and len(repilot_successes) == 3:
        compatibility_status = "temperature_omitted_structured_output_verified_3_of_3"
    return {
        "sources": [
            str(PILOT_RECORDS.relative_to(REPO)),
            str(REPILOT_RECORDS.relative_to(REPO)),
        ],
        "kind": "real_structured_compatibility_pilot",
        "attempted_calls": sum(row.get("status") != "skipped_model_parameter_failure" for row in rows),
        "successful_calls": len(successes),
        "validation_errors": [row.get("error") for row in validation],
        "repilot_successful_structured_calls": len(repilot_successes),
        "access_eligible": access_eligible,
        "compatibility_verified": bool(successes) or (
            spec["alias"] == "kimi_k3" and len(repilot_successes) == 3
        ),
        "compatibility_status": compatibility_status,
    }


def _removed_grok_evidence(access: dict[str, Any], pilot: list[dict[str, Any]]) -> dict[str, Any]:
    rows = [row for row in pilot if row.get("model_id") == REMOVED_MODEL["callable_model_id"]]
    denied = [row for row in rows if (row.get("error") or {}).get("code") == "AccessDeniedException"]
    return {
        **REMOVED_MODEL,
        "decision": "removed",
        "reason": "real Converse calls returned AccessDeniedException despite AVAILABLE control-plane metadata",
        "control_plane_access": access["models"].get(REMOVED_MODEL["base_model_id"]),
        "invoke_evidence": {
            "source": str(PILOT_RECORDS.relative_to(REPO)),
            "attempted_calls": len(rows),
            "access_denied_calls": len(denied),
            "errors": [row.get("error") for row in denied],
            "access_eligible": False,
        },
    }


def build_verification() -> dict[str, Any]:
    observations: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    target_price_keys = {(row["provider"], row["pricing_model"]) for row in MODELS}
    sources = []
    for path in sorted(PRICING_DIR.glob("*.json")):
        snapshot = json.loads(path.read_text())
        sources.append({
            "path": str(path.relative_to(REPO)),
            "sha256": sha256(path),
            "source_url": _price_url(snapshot),
            "retrieved": RETRIEVED,
        })
        for sku, product in snapshot["products"].items():
            attributes = product.get("attributes", {})
            if (attributes.get("provider"), attributes.get("model")) not in target_price_keys:
                continue
            if not _regional_standard(attributes):
                continue
            direction = "input" if attributes["inferenceType"].casefold() == "input tokens" else "output"
            observations[(attributes.get("provider", ""), attributes.get("model", ""), direction)].append({
                "sku": sku,
                "price_per_mtok": _per_million(snapshot, sku),
                "snapshot": str(path.relative_to(REPO)),
                "usage_type": attributes.get("usagetype"),
                "service_tier": attributes.get("service_tier"),
            })

    access = json.loads(ACCESS.read_text())
    probe = json.loads(MODEL_PROBE.read_text())
    pilot = _read_jsonl(PILOT_RECORDS)
    repilot = _read_jsonl(REPILOT_RECORDS)
    verified = []
    for spec in MODELS:
        prices = {}
        evidence = {}
        for direction in ("input", "output"):
            rows = observations.get((spec["provider"], spec["pricing_model"], direction), [])
            values = sorted({row["price_per_mtok"] for row in rows})
            if len(values) != 1:
                raise ValueError(
                    f"{spec['base_model_id']}: expected one {direction} price, got {values}"
                )
            prices[direction] = values[0]
            evidence[direction] = rows
        if prices["input"] != spec["expected_input_per_mtok"]:
            raise ValueError(f"{spec['base_model_id']}: unexpected input price")
        if prices["output"] != spec["expected_output_per_mtok"]:
            raise ValueError(f"{spec['base_model_id']}: unexpected output price")

        raw_access = access["models"].get(spec["base_model_id"])
        if raw_access is None:
            raise ValueError(f"{spec['base_model_id']}: missing from access snapshot")
        checks = {
            "agreement": (raw_access.get("agreementAvailability") or {}).get("status") == "AVAILABLE",
            "authorization": raw_access.get("authorizationStatus") == "AUTHORIZED",
            "entitlement": raw_access.get("entitlementAvailability") == "AVAILABLE",
            "region": raw_access.get("regionAvailability") == "AVAILABLE",
        }
        invoke_access = _invoke_evidence(spec, pilot, repilot, probe)
        verified.append({
            **spec,
            "input_per_mtok": prices["input"],
            "output_per_mtok": prices["output"],
            "blended_per_mtok": (3 * prices["input"] + prices["output"]) / 4,
            "price_basis": "us-east-1 regional (Geo CRIS where applicable), standard on-demand",
            "price_evidence": evidence,
            "access": raw_access,
            "control_plane_access_checks": checks,
            "invoke_access": invoke_access,
            "verified": (
                all(checks.values())
                and invoke_access["access_eligible"]
                and invoke_access["compatibility_verified"]
            ),
        })

    if not all(row["verified"] for row in verified):
        raise ValueError("one or more final models is not available on this account")
    return {
        "protocol": "price-matched-v2",
        "generated_offline": True,
        "status": "verified_from_saved_prices_control_plane_and_real_invoke_evidence",
        "eligibility_rule": "regional standard price plus saved real Converse evidence; control-plane availability alone is insufficient",
        "inputs": {
            "pricing_snapshots": sources,
            "access_snapshot": {
                "path": str(ACCESS.relative_to(REPO)),
                "sha256": sha256(ACCESS),
                "checked_at": access["checked_at"],
                "api": access["api"],
            },
            "invoke_probe": {
                "path": str(MODEL_PROBE.relative_to(REPO)),
                "sha256": sha256(MODEL_PROBE),
                "probed_at": probe["probed_at"],
            },
            "compatibility_pilot_records": {
                "path": str(PILOT_RECORDS.relative_to(REPO)),
                "sha256": sha256(PILOT_RECORDS),
            },
            "compatibility_repilot_records": {
                "path": str(REPILOT_RECORDS.relative_to(REPO)),
                "sha256": sha256(REPILOT_RECORDS),
            },
        },
        "models": verified,
        "removed_models": [_removed_grok_evidence(access, pilot)],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    result = build_verification()
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.check:
        if not OUT.exists() or OUT.read_text() != payload:
            raise SystemExit("price-matched model verification output is missing or stale")
    else:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(payload)
    print(json.dumps({
        "status": result["status"],
        "models": [
            {
                "id": row["callable_model_id"],
                "input": row["input_per_mtok"],
                "output": row["output_per_mtok"],
                "blended": row["blended_per_mtok"],
                "verified": row["verified"],
            }
            for row in result["models"]
        ],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
