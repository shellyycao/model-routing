"""Offline tests: provenance hashes, run IDs, and manual-pricing rules."""

from __future__ import annotations

import hashlib

import pytest
import yaml

from src.bedrock.models import DEFAULT_MODELS_CONFIG, Pricing, PricingConfigError, load_registry
from src.bedrock.provenance import (
    canonical_json,
    config_hash,
    hash_file,
    hash_json,
    hash_tree,
    make_run_id,
    models_fingerprint,
)


# ------------------------------------------------------------------ hashing
def test_hash_file_matches_sha256(tmp_path):
    p = tmp_path / "d.csv"
    p.write_bytes(b"a,b\n1,2\n")
    assert hash_file(p) == hashlib.sha256(b"a,b\n1,2\n").hexdigest()


def test_hash_json_is_canonical():
    assert hash_json({"b": 1, "a": [1, {"y": 2, "x": 1}]}) == hash_json({"a": [1, {"x": 1, "y": 2}], "b": 1})
    assert canonical_json({"b": 1, "a": "é"}) == '{"a":"é","b":1}'
    assert hash_json({"a": 1}) != hash_json({"a": 2})


def test_hash_json_rejects_unstable_inputs():
    with pytest.raises(ValueError):
        hash_json({"x": float("nan")})
    with pytest.raises(TypeError):
        hash_json({1: "non-str key"})
    with pytest.raises(TypeError):
        hash_json({"s": {1, 2}})


def test_hash_tree_independent_of_location(tmp_path):
    for root in ("r1", "r2"):
        (tmp_path / root / "sub").mkdir(parents=True)
        (tmp_path / root / "a.txt").write_text("A")
        (tmp_path / root / "sub" / "b.txt").write_text("B")
    assert hash_tree(tmp_path / "r1") == hash_tree(tmp_path / "r2")
    (tmp_path / "r2" / "sub" / "b.txt").write_text("B2")
    assert hash_tree(tmp_path / "r1") != hash_tree(tmp_path / "r2")


# ------------------------------------------------------------------ config hash / run id
def test_config_hash_deterministic_and_sensitive():
    reg = load_registry()
    h = config_hash(reg, "v1", "d" * 64)
    assert h == config_hash(load_registry(), "v1", "d" * 64) and len(h) == 64
    assert h != config_hash(reg, "v2", "d" * 64)
    assert h != config_hash(reg, "v1", "e" * 64)
    assert h != config_hash(reg, "v1", "d" * 64, extra={"path": "A-B-C"})
    assert config_hash(reg, "v1", "d", extra={"a": 1, "b": 2}) == config_hash(reg, "v1", "d", extra={"b": 2, "a": 1})


def test_config_hash_accepts_path_and_ignores_pricing_and_pacing():
    reg = load_registry()
    base = config_hash(reg, "v1", "d")
    assert config_hash(DEFAULT_MODELS_CONFIG, "v1", "d") == base
    reg.models["A"].pricing = Pricing(input_per_mtok=1, output_per_mtok=2, source="SYNTHETIC_FIXTURE",
                                      retrieved="2026-01-01")
    reg.concurrency.max_workers = 99
    assert config_hash(reg, "v1", "d") == base  # filling a price must not re-run completed work


def test_config_hash_sensitive_to_model_behaviour():
    reg = load_registry()
    base = config_hash(reg, "v1", "d")
    reg.models["A"].inference.temperature = 0.7
    assert config_hash(reg, "v1", "d") != base
    reg2 = load_registry()
    reg2.models["B"].model_id = "us.amazon.nova-lite-v1:0"
    assert config_hash(reg2, "v1", "d") != base
    assert set(models_fingerprint(reg2)) == {"region", "models"}


def test_make_run_id_deterministic():
    reg = load_registry()
    a = make_run_id("exp1", reg, "v1", "d", extra={"project": "p1"})
    assert a == make_run_id("exp1", load_registry(), "v1", "d", extra={"project": "p1"})
    assert a.startswith("exp1-") and len(a) == len("exp1-") + 16
    assert a != make_run_id("exp2", reg, "v1", "d", extra={"project": "p1"})
    assert a != make_run_id("exp1", reg, "v1", "d", extra={"project": "p2"})
    with pytest.raises(ValueError):
        make_run_id("bad id", reg, "v1", "d")


# ------------------------------------------------------------------ manual pricing (task 4)
def _write_cfg(tmp_path, pricing_a):
    raw = yaml.safe_load(DEFAULT_MODELS_CONFIG.read_text())
    raw["models"]["A"]["pricing"] = pricing_a
    for alias in ("B", "C"):
        raw["models"][alias]["pricing"] = {
            "input_per_mtok": None,
            "output_per_mtok": None,
            "source": None,
            "retrieved": None,
        }
    p = tmp_path / "models.yaml"
    p.write_text(yaml.safe_dump(raw))
    return p


@pytest.mark.parametrize("pricing,msg", [
    ({"input_per_mtok": 1.0, "output_per_mtok": 2.0, "source": None, "retrieved": "2026-01-01"}, "source"),
    ({"input_per_mtok": 1.0, "output_per_mtok": 2.0, "source": "  ", "retrieved": "2026-01-01"}, "source"),
    ({"input_per_mtok": 1.0, "output_per_mtok": 2.0, "source": "x", "retrieved": None}, "retrieved"),
    ({"input_per_mtok": 1.0, "output_per_mtok": 2.0, "source": "x", "retrieved": "last week"}, "retrieved"),
    ({"input_per_mtok": 1.0, "output_per_mtok": None, "source": "x", "retrieved": "2026-01-01"}, "both"),
    ({"input_per_mtok": -1.0, "output_per_mtok": 2.0, "source": "x", "retrieved": "2026-01-01"}, ">= 0"),
])
def test_loading_rejects_price_without_provenance(tmp_path, pricing, msg):
    with pytest.raises(PricingConfigError, match=msg):
        load_registry(_write_cfg(tmp_path, pricing))


def test_loading_accepts_documented_price(tmp_path):
    reg = load_registry(_write_cfg(tmp_path, {
        "input_per_mtok": 1.0, "output_per_mtok": 2.0,
        "source": "SYNTHETIC_FIXTURE", "retrieved": "2026-01-01"}))
    st = reg.pricing_status()
    assert st["priced"] == ["A"] and st["unpriced"] == ["B", "C"] and not st["all_priced"]
    assert st["models"]["A"]["source"] == "SYNTHETIC_FIXTURE" and st["models"]["A"]["retrieved"] == "2026-01-01"


def test_repo_pricing_status_is_verified():
    st = load_registry().pricing_status()
    assert st["all_priced"] is True and st["dollar_guard_possible"] is True
    assert st["priced"] == ["A", "B", "C"] and st["unpriced"] == []
    assert all(st["models"][alias]["retrieved"] == "2026-11-18" for alias in ("A", "B", "C"))
