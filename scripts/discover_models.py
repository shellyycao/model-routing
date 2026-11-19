"""Discover Bedrock text models and system inference profiles (control plane, free).

Writes results/raw/model_discovery_<YYYY-MM-DD>.json (UTC date) with the region, text
models (lifecycle status, inference types), system inference profiles, and whether each
configured study model (configs/models.yaml) is present, ACTIVE and callable as configured.

Usage:
  .venv/bin/python scripts/discover_models.py [--out PATH]
  RUN_LIVE=1 .venv/bin/python scripts/discover_models.py --probe   # PAID: 1 tiny call per study model

Credentials come only from the AWS profile in configs/models.yaml; they are never read,
printed or stored by this script. Account IDs are redacted from all output.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.bedrock.discovery import build_report, redact  # noqa: E402
from src.bedrock.models import REPO_ROOT, load_registry  # noqa: E402

PROBE_MAX_TOKENS = 256  # reasoning models spend output tokens before the answer


def probe(registry) -> dict:
    """Minimal live inference check: one call per study model, hard-capped. PAID."""
    from src.bedrock.client import BedrockClient, ModelInvocationError
    from src.bedrock.usage import InvocationContext, UsageLimits

    n = len(registry.models)
    client = BedrockClient(
        registry,
        log_path=REPO_ROOT / "results" / "raw" / "invocations.jsonl",
        ledger_path=REPO_ROOT / "results" / "raw" / "discovery_probe_ledger.json",
        cache_dir=None,
        limits=UsageLimits(max_calls=n, max_input_tokens=200 * n, max_output_tokens=PROBE_MAX_TOKENS * n),
    )
    out = {}
    for alias in registry.aliases:
        ctx = InvocationContext(experiment_id="model_discovery_probe", stage_id="probe", prompt_version="probe.v1")
        try:
            r = client.converse(alias, "Reply with exactly: OK", context=ctx, use_cache=False,
                                max_tokens=PROBE_MAX_TOKENS)
            out[alias] = {"status": r.record.status, "stop_reason": r.record.stop_reason,
                          "truncated": r.record.truncated, "invocation_id": r.record.invocation_id,
                          "text_prefix": r.text.strip()[:20]}
        except ModelInvocationError as e:
            out[alias] = {"status": e.record.status, "invocation_id": e.record.invocation_id,
                          "error": e.record.error}
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default=str(REPO_ROOT / "configs" / "models.yaml"))
    ap.add_argument("--out", default=None, help="output JSON path (default results/raw/model_discovery_<date>.json)")
    ap.add_argument("--probe", action="store_true", help="PAID: one tiny inference per study model; needs RUN_LIVE=1")
    args = ap.parse_args(argv)

    if args.probe and os.environ.get("RUN_LIVE") != "1":
        print("Refusing --probe: it makes paid Bedrock calls. Set RUN_LIVE=1 to allow.", file=sys.stderr)
        return 2

    import boto3
    from botocore.exceptions import BotoCoreError, ClientError

    registry = load_registry(args.config)
    now = datetime.now(timezone.utc)
    out = Path(args.out) if args.out else REPO_ROOT / "results" / "raw" / f"model_discovery_{now.date().isoformat()}.json"
    try:
        session = boto3.Session(profile_name=registry.aws_profile, region_name=registry.region)
        report = build_report(registry, session.client("bedrock"), generated_at=now.isoformat())
    except ClientError as e:
        err = e.response.get("Error", {})
        print(redact(f"Discovery failed: {err.get('Code')}: {err.get('Message')}"), file=sys.stderr)
        return 1
    except BotoCoreError as e:
        print(redact(f"Discovery failed: {type(e).__name__}: {e}"), file=sys.stderr)
        return 1

    if args.probe:
        report["probe"] = redact(probe(registry))

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")

    c = report["counts"]
    print(f"region={report['region']} text_models={c['text_models']} (active {c['text_models_active']}) "
          f"system_profiles={c['system_inference_profiles']}")
    for alias, e in report["study_models"].items():
        print(f"  {alias}: {e['model_id']:<34} kind={e['id_kind']:<25} status={e['status']} "
              f"base_lifecycle={e['base_model_lifecycle']} callable_as_configured={e['callable_as_configured']}")
    if "probe" in report:
        for alias, p in report["probe"].items():
            print(f"  probe {alias}: {p['status']}")
    print(f"wrote {out.relative_to(REPO_ROOT) if out.is_relative_to(REPO_ROOT) else out}")
    return 0 if report["all_study_models_ok"] else 3


if __name__ == "__main__":
    sys.exit(main())
