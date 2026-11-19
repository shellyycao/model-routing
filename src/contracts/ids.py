"""Identifiers shared by every module: stages, model aliases, and workflow paths."""

from __future__ import annotations

import re
from enum import Enum
from itertools import product


class StageId(str, Enum):
    CLEANING = "cleaning"
    ANALYSIS = "analysis"
    REPORTING = "reporting"


# Canonical stage order. Development sequence may use the first two only.
STAGES: tuple[StageId, ...] = (StageId.CLEANING, StageId.ANALYSIS, StageId.REPORTING)

# Model aliases are defined in configs/models.yaml (A, B, C).
PATH_SEP = "-"


def make_path_id(models: tuple[str, ...] | list[str]) -> str:
    """('A','B','C') -> 'A-B-C'. Position i is the model for STAGES[i]."""
    return PATH_SEP.join(models)


_ALIAS_OK = re.compile(r"^[A-Z]$")


def parse_path_id(path_id: str) -> tuple[str, ...]:
    parts = tuple(path_id.split(PATH_SEP))
    if not (1 <= len(parts) <= len(STAGES)) or not all(_ALIAS_OK.match(a) for a in parts):
        raise ValueError(f"Invalid path_id {path_id!r}: expected 1-{len(STAGES)} single-letter aliases joined by '{PATH_SEP}'")
    return parts


def enumerate_paths(aliases: list[str], n_stages: int = len(STAGES)) -> list[str]:
    """All |aliases|^n_stages paths via Cartesian product (never hard-coded)."""
    return [make_path_id(p) for p in product(sorted(aliases), repeat=n_stages)]


def n_switches(path_id: str) -> int:
    m = parse_path_id(path_id)
    return sum(1 for a, b in zip(m, m[1:]) if a != b)


def is_single_model(path_id: str) -> bool:
    return n_switches(path_id) == 0
