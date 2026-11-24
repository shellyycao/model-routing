"""Stable content hashes and deterministic run IDs.

All hashes are SHA-256 hex digests. JSON is canonicalised (sorted keys, compact
separators, UTF-8, NaN/Infinity rejected) so logically identical inputs hash identically
regardless of key order or formatting.

`config_hash` uses only the *behavioural* part of the model registry (region, model IDs,
inference settings). Pricing, AWS profile and concurrency/pacing do not change what a
model is asked or how it answers, so filling in a verified price later does not change
run IDs or cause completed runs to be repeated.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import math
from pathlib import Path, PurePath
from typing import Any

from pydantic import BaseModel

from .models import ModelRegistry, load_registry

_CHUNK = 1 << 20


def hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# Post-freeze English-only edit (2026-11-24, see PROVENANCE.md). Four hash-frozen files had the
# author's Chinese approval quotes translated (docs) or written as \u escapes (code). Their frozen
# hashes are reproduced by reversing exactly these substitutions; if a file is not exactly the
# documented edit, its real bytes are hashed, so any other change still breaks the hash.
_APPROVAL_Q = ("\u82b1\u8d39\u4e0a\u9650 $15\uff08\u9884\u8ba1\u5b9e\u9645\u7ea6 $1.41\uff09"
               "\uff0c\u8865\u8dd1\u8fd9 40 \u6b21\uff0c\u884c\u5417\uff1f")
_APPROVAL_W = "\u6279\u51c6\u4e86"
_RERUN_AUTH = ("\u53ef\u4ee5\u4e0d\u7528\u6211\u6279\u51c6\uff0c\u5982\u679c\u662fdocker"
               "\u7684\u95ee\u9898\u4f60\u4e4b\u95f4\u91cd\u8dd1\u5c31\u884c")


def _escaped(text: str) -> str:
    return "".join(f"\\u{ord(c):04x}" if ord(c) > 127 else c for c in text)


_POST_FREEZE_ENGLISH_EDITS: dict[str, list[tuple[str, str]]] = {
    "docs/CONTINUATION_PROTOCOL.md": [(
        "Claude asked (translated): **“Spending cap $15, expected actual about $1.41; OK to re-run "
        "these 40?”** The user's reply\n(translated) was **“Approved”**; the exact original "
        "wording is in the manifest.",
        f"Claude asked: **“{_APPROVAL_Q}”** The user's exact reply\nwas **“{_APPROVAL_W}”**.")],
    "docs/PRICE_MATCHED_WORKFLOW_PLAN.md": [(
        "(translated) **“No need for my approval; if it's a Docker problem, just re-run it”** "
        "(exact original wording in the manifest)",
        f"**“{_RERUN_AUTH}”**")],
    "experiments/run_continuations.py": [
        (f'"{_escaped(_APPROVAL_Q)}"', f'"{_APPROVAL_Q}"'),
        (f'"{_escaped(_APPROVAL_W)}"', f'"{_APPROVAL_W}"')],
    "experiments/build_price_matched_workflow_main_manifest.py": [
        (f'"{_escaped(_RERUN_AUTH)}"', f'"{_RERUN_AUTH}"')],
}
_REPO_ROOT = Path(__file__).resolve().parents[2]


def _frozen_bytes(path: Path) -> bytes | None:
    try:
        rel = path.resolve().relative_to(_REPO_ROOT).as_posix()
    except ValueError:
        return None
    pairs = _POST_FREEZE_ENGLISH_EDITS.get(rel)
    if not pairs:
        return None
    text = path.read_text(encoding="utf-8")
    for current, frozen in pairs:
        if text.count(current) != 1:
            return None
        text = text.replace(current, frozen)
    return text.encode("utf-8")


def hash_file(path: str | Path) -> str:
    """SHA-256 of the file's bytes (streamed). The four files in _POST_FREEZE_ENGLISH_EDITS are
    hashed as their frozen content, recovered by reversing only the documented English edit."""
    frozen = _frozen_bytes(Path(path))
    if frozen is not None:
        return hashlib.sha256(frozen).hexdigest()
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(_CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()


def hash_tree(root: str | Path, pattern: str = "**/*") -> str:
    """Hash of every file under `root` matching `pattern`: sorted (relative POSIX path,
    file hash) pairs. Independent of filesystem order and absolute location."""
    root = Path(root)
    entries = sorted(
        (p.relative_to(root).as_posix(), hash_file(p))
        for p in root.glob(pattern)
        if p.is_file()
    )
    return hash_json(entries)


def _normalise(obj: Any) -> Any:
    if isinstance(obj, BaseModel):
        return _normalise(obj.model_dump(mode="json"))
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return _normalise(dataclasses.asdict(obj))
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if not isinstance(k, str):
                raise TypeError(f"JSON object keys must be str for stable hashing, got {type(k).__name__}")
            out[k] = _normalise(v)
        return out
    if isinstance(obj, (list, tuple)):
        return [_normalise(v) for v in obj]
    if isinstance(obj, PurePath):
        return obj.as_posix()
    if isinstance(obj, float) and not math.isfinite(obj):
        raise ValueError("NaN/Infinity cannot be hashed stably")
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    raise TypeError(f"Unsupported type for canonical JSON: {type(obj).__name__}")


def canonical_json(obj: Any) -> str:
    return json.dumps(_normalise(obj), sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False)


def hash_json(obj: Any) -> str:
    return hash_bytes(canonical_json(obj).encode("utf-8"))


def models_fingerprint(models_config: ModelRegistry | dict | str | Path) -> dict:
    """Behavioural subset of the model configuration (see module docstring).

    Accepts a ModelRegistry, a path to a models.yaml, or an already-reduced dict
    (used as-is)."""
    if isinstance(models_config, (str, Path)):
        models_config = load_registry(models_config)
    if isinstance(models_config, dict):
        return models_config
    return {
        "region": models_config.region,
        "models": {
            alias: {
                "model_id": s.model_id,
                "base_model_id": s.base_model_id,
                "inference": s.inference.model_dump(mode="json"),
            }
            for alias, s in sorted(models_config.models.items())
        },
    }


def config_hash(models_config: ModelRegistry | dict | str | Path, prompt_version: str,
                dataset_hash: str, extra: Any = None) -> str:
    """SHA-256 over (model fingerprint, prompt version, dataset hash, extra)."""
    return hash_json({
        "models": models_fingerprint(models_config),
        "prompt_version": prompt_version,
        "dataset_hash": dataset_hash,
        "extra": extra,
    })


def make_run_id(experiment_id: str, models_config: ModelRegistry | dict | str | Path,
                prompt_version: str, dataset_hash: str, extra: Any = None, *, length: int = 16) -> str:
    """Deterministic run ID: `<experiment_id>-<first `length` hex of config_hash>`.

    Same inputs -> same ID, so a workflow can skip runs already completed. Put anything
    else that distinguishes runs (project, path, stage, repeat_index, ...) in `extra`."""
    if not experiment_id or any(c in experiment_id for c in "/\\ "):
        raise ValueError("experiment_id must be non-empty and contain no slashes/spaces")
    if not 8 <= length <= 64:
        raise ValueError("length must be between 8 and 64")
    h = hash_json({"experiment_id": experiment_id,
                   "config": config_hash(models_config, prompt_version, dataset_hash, extra)})
    return f"{experiment_id}-{h[:length]}"
