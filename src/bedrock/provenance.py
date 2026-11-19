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


def hash_file(path: str | Path) -> str:
    """SHA-256 of the file's bytes (streamed)."""
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
