"""Deterministic post-hoc / exploratory analysis for Independent-v2.

Rules: docs/POSTHOC_V2_RULES.md. This module is offline and never calls a model.
Processed JSON remains blinded; model names appear only in the final Markdown report.
"""

from __future__ import annotations

import collections
import hashlib
import json
from pathlib import Path

from experiments import run_independent_v2_benchmark as runner
from src.bedrock.models import load_registry
from src.independent.v2_posthoc import (
    bootstrap_paired_difference,
    classify_a2_error,
    comparison_seed,
    exact_mcnemar,
    holm_adjust,
    score_a1_locations,
    score_a3_deduplicated,
    score_a3_grounding,
    wilcoxon_approx,
)


REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "results/raw/independent_v2"
OUT = REPO / "results/processed/independent_v2/posthoc.json"
REPORT = REPO / "results/reports/independent_v2_posthoc.md"
RULES = REPO / "docs/POSTHOC_V2_RULES.md"
ALIASES = ("A", "B", "C")
PAIRS = (("A", "B"), ("A", "C"), ("B", "C"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def load_inputs() -> tuple[dict[str, list[dict]], dict[str, dict], dict[str, str]]:
    records, sources = {}, {}
    for task, experiment_id in runner.EXPERIMENT_IDS.items():
        path = RAW / f"{experiment_id}.jsonl"
        records[task] = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
        sources[str(path.relative_to(REPO))] = sha256(path)
    cases = {
        task: {case["case_id"]: case for case in runner.load_cases(task)}
        for task in ("a1", "a2", "a3")
    }
    for path in (
        REPO / "src/independent/v2.py",
        REPO / "src/independent/v2_posthoc.py",
        Path(__file__),
        RULES,
        REPO / "docs/POSTHOC_V2_ANALYSIS_BRIEF.md",
        REPO / "docs/MANAGER_CHECKPOINTS.md",
        REPO / "docs/reviews/2026-11-18_posthoc_rules_checkpoint1_review.md",
    ):
        sources[str(path.relative_to(REPO))] = sha256(path)
    return records, cases, sources


def parsed_response(row: dict) -> dict | None:
    candidates = [REPO / artifact for artifact in row.get("artifacts", []) if artifact.endswith("parsed.json")]
    return json.loads(candidates[0].read_text()) if candidates and candidates[0].is_file() else None


def build_record_views(records: dict[str, list[dict]], cases: dict[str, dict]) -> dict[str, list[dict]]:
    views: dict[str, list[dict]] = {task: [] for task in records}
    for task, rows in records.items():
        for row in rows:
            case = cases[task][row["case_id"]]
            response = parsed_response(row)
            base = {
                "case_id": row["case_id"],
                "alias": row["model_alias"],
                "difficulty": row["scores"]["difficulty"],
            }
            if task == "a1":
                base.update({
                    "frozen_functional_correct": bool(row["scores"]["functional_correct"]),
                    "frozen_bug_location_recall": float(row["scores"]["bug_location_recall"]),
                    "posthoc_location": score_a1_locations(case, response),
                })
            elif task == "a2":
                errors = []
                for field, label in sorted((row["scores"].get("per_field") or {}).items()):
                    if label in {"wrong_value", "missed", "hallucinated"}:
                        errors.append({
                            "field": field,
                            "frozen_label": label,
                            "manual_category": classify_a2_error(case, field),
                        })
                base.update({
                    "frozen_content_correct": bool(row["scores"]["content_correct"]),
                    "errors": errors,
                })
            else:
                ranking_valid = bool(row["scores"].get("ranking_valid"))
                frozen_ndcg = float(row["scores"].get("ndcg_at_5", 0.0))
                frozen_recall = float(row["scores"].get("grade2_recall_at_5", 0.0))
                deduplicated = score_a3_deduplicated(case, response)
                grounding = score_a3_grounding(case, response)
                base.update({
                    "ranking_valid": ranking_valid,
                    "ranking": {
                        "frozen_all_case": frozen_ndcg,
                        "valid_ranking_only": frozen_ndcg if ranking_valid else None,
                        "strict_invalid_zero": frozen_ndcg if ranking_valid else 0.0,
                        "deduplicated_first5": deduplicated["ndcg_at_5"],
                    },
                    "grade2_recall": {
                        "frozen_all_case": frozen_recall,
                        "valid_ranking_only": frozen_recall if ranking_valid else None,
                        "strict_invalid_zero": frozen_recall if ranking_valid else 0.0,
                        "deduplicated_first5": deduplicated["grade2_recall_at_5"],
                    },
                    "grounding": {
                        "frozen_stored": float(row["scores"].get("evidence_grounding", 0.0)),
                        **grounding,
                    },
                })
            views[task].append(base)
    return views


def summarize(views: dict[str, list[dict]]) -> dict:
    cells = {}
    for task, rows in views.items():
        for alias in ALIASES:
            subset = [row for row in rows if row["alias"] == alias]
            cell = {"task": task, "alias": alias, "n": len(subset)}
            if task == "a1":
                cell.update({
                    "frozen_functional_correct_rate": mean([
                        float(row["frozen_functional_correct"]) for row in subset
                    ]),
                    "frozen_bug_location_recall": mean([
                        row["frozen_bug_location_recall"] for row in subset
                    ]),
                    "normalized_location_recall": mean([
                        row["posthoc_location"]["normalized_location_recall"] for row in subset
                    ]),
                    "wrong_location": sum(row["posthoc_location"]["wrong_location"] for row in subset),
                    "format_mismatch": sum(row["posthoc_location"]["format_mismatch"] for row in subset),
                    "bare_range_only_match": sum(
                        row["posthoc_location"]["bare_range_only_match"] for row in subset
                    ),
                    "fixed_span_only_match": sum(
                        row["posthoc_location"]["fixed_span_only_match"] for row in subset
                    ),
                })
            elif task == "a2":
                errors = [error for row in subset for error in row["errors"]]
                cell.update({
                    "frozen_content_correct_rate": mean([
                        float(row["frozen_content_correct"]) for row in subset
                    ]),
                    "error_count": len(errors),
                    "frozen_label_counts": dict(collections.Counter(error["frozen_label"] for error in errors)),
                    "manual_category_counts": dict(collections.Counter(
                        error["manual_category"] for error in errors
                    )),
                    "error_crosstab": {
                        f"{label}|{category}": count
                        for (label, category), count in sorted(collections.Counter(
                            (error["frozen_label"], error["manual_category"]) for error in errors
                        ).items())
                    },
                })
            else:
                ranking = {}
                recall = {}
                for name in (
                    "frozen_all_case", "valid_ranking_only", "strict_invalid_zero", "deduplicated_first5"
                ):
                    ranking[name] = mean([
                        row["ranking"][name] for row in subset if row["ranking"][name] is not None
                    ])
                    recall[name] = mean([
                        row["grade2_recall"][name]
                        for row in subset if row["grade2_recall"][name] is not None
                    ])
                failure_counts = collections.Counter()
                for row in subset:
                    failure_counts.update(row["grounding"]["frozen_failure_reasons"])
                cell.update({
                    "ranking_valid": sum(row["ranking_valid"] for row in subset),
                    "ranking_ndcg": ranking,
                    "grade2_recall": recall,
                    "frozen_ndcg_over_one": sum(
                        row["ranking"]["frozen_all_case"] > 1.0 + 1e-12 for row in subset
                    ),
                    "frozen_recall_over_one": sum(
                        row["grade2_recall"]["frozen_all_case"] > 1.0 + 1e-12 for row in subset
                    ),
                    "grounding": {
                        "frozen_stored": mean([row["grounding"]["frozen_stored"] for row in subset]),
                        "frozen_recomputed": mean([
                            row["grounding"]["frozen_recomputed"] for row in subset
                        ]),
                        "relaxed_r1": mean([row["grounding"]["relaxed_r1"] for row in subset]),
                        "relaxed_r2": mean([row["grounding"]["relaxed_r2"] for row in subset]),
                        "attribute_key_coverage": mean([
                            row["grounding"]["attribute_key_coverage"] for row in subset
                        ]),
                        "failure_reasons": dict(failure_counts),
                    },
                })
            cells[f"{task}|{alias}"] = cell
    return cells


def _paired(rows: list[dict], alias: str, field) -> list:
    return [field(row) for row in sorted(rows, key=lambda row: row["case_id"]) if row["alias"] == alias]


def paired_statistics(views: dict[str, list[dict]]) -> dict:
    result = {"a1": {}, "a2": {}, "a3": {}}
    binary_specs = {
        "a1": ("functional_correct", lambda row: bool(row["frozen_functional_correct"])),
        "a2": ("content_correct", lambda row: bool(row["frozen_content_correct"])),
    }
    for task, (view_name, getter) in binary_specs.items():
        raw_p = []
        for first, second in PAIRS:
            pair = f"{first}-{second}"
            x = _paired(views[task], first, getter)
            y = _paired(views[task], second, getter)
            mcnemar = exact_mcnemar(x, y)
            bootstrap = bootstrap_paired_difference(
                [float(value) for value in x], [float(value) for value in y],
                seed=comparison_seed(task, view_name, pair),
            )
            result[task][pair] = {
                "view": view_name,
                "first_mean": mean([float(value) for value in x]),
                "second_mean": mean([float(value) for value in y]),
                **mcnemar,
                **bootstrap,
            }
            raw_p.append((pair, mcnemar["p_value"]))
        adjusted = holm_adjust(raw_p)
        for pair, value in adjusted.items():
            result[task][pair]["holm_p"] = value

    a3_p = []
    for view_name in ("frozen_all_case", "strict_invalid_zero", "deduplicated_first5"):
        result["a3"][view_name] = {}
        for first, second in PAIRS:
            pair = f"{first}-{second}"
            getter = lambda row, view=view_name: float(row["ranking"][view])
            x = _paired(views["a3"], first, getter)
            y = _paired(views["a3"], second, getter)
            bootstrap = bootstrap_paired_difference(
                x, y, seed=comparison_seed("a3", view_name, pair)
            )
            wilcoxon = wilcoxon_approx(x, y)
            result["a3"][view_name][pair] = {
                "first_mean": mean(x), "second_mean": mean(y), **bootstrap, **wilcoxon,
            }
            a3_p.append((f"{view_name}|{pair}", wilcoxon["p_value"]))
    adjusted = holm_adjust(a3_p)
    for key, value in adjusted.items():
        view_name, pair = key.split("|", 1)
        result["a3"][view_name][pair]["holm_p"] = value
    return result


def analyze() -> dict:
    records, cases, sources = load_inputs()
    views = build_record_views(records, cases)
    result = {
        "analysis_version": "independent-v2-posthoc-1.0",
        "label": "post-hoc / exploratory",
        "rules_version": "posthoc-v2-rules-1.0.1",
        "analysis_date": "2026-11-18",
        "blinded": True,
        "aliases": list(ALIASES),
        "source_hashes": sources,
        "implementation": {
            "bootstrap_draws": 10_000,
            "wilcoxon": "stdlib tie-corrected normal approximation; zeros dropped; no continuity correction",
            "scipy_version": None,
            "scipy_status": "not installed in project environment",
        },
        "record_views": views,
        "cells": summarize(views),
        "paired_statistics": paired_statistics(views),
    }
    registry = load_registry()
    serialized = json.dumps(result, sort_keys=True)
    forbidden = [spec.name for spec in registry.models.values()] + [spec.model_id for spec in registry.models.values()]
    if any(value in serialized for value in forbidden):
        raise ValueError("blinded processed result contains a model name or ID")
    return result


def pct(value: float | None) -> str:
    return "—" if value is None else f"{100 * value:.1f}%"


def num(value: float | None, digits: int = 3) -> str:
    return "—" if value is None else f"{value:.{digits}f}"


def render_report(result: dict) -> str:
    registry = load_registry()
    names = {alias: registry.get(alias).name for alias in ALIASES}
    cells, statistics = result["cells"], result["paired_statistics"]
    lines = [
        "# Independent Benchmark v2 Post-hoc / Exploratory Analysis",
        "",
        "**Status:** post-hoc / exploratory; not prospectively registered  ",
        "**Rules:** `posthoc-v2-rules-1.0.1`, committed before rescoring  ",
        "**Frozen results remain unchanged.**",
        "",
        "The base rules were committed before post-hoc computation. Implementation began before the manager's CP1 "
        "review was relayed, but no rescoring had been run; the required R-1 disclosure and R-2 implementation "
        "amendment were handled before this report was computed.",
        "",
        "## Prospective frozen results",
        "",
        "The frozen primary outcomes are repeated for context; none is replaced by a relaxed view.",
        "",
        "| Task | Model | Frozen primary |",
        "|---|---|---:|",
    ]
    for alias in ALIASES:
        lines.append(f"| A1 | {names[alias]} | {pct(cells[f'a1|{alias}']['frozen_functional_correct_rate'])} |")
    for alias in ALIASES:
        lines.append(f"| A2 | {names[alias]} | {pct(cells[f'a2|{alias}']['frozen_content_correct_rate'])} |")
    for alias in ALIASES:
        lines.append(f"| A3 | {names[alias]} | nDCG {num(cells[f'a3|{alias}']['ranking_ndcg']['frozen_all_case'])} |")

    lines += [
        "",
        "## A1 location-format sensitivity",
        "",
        "The normalized rule credits a gold semantic region when the response identifies its containing function "
        "by name or by an overlapping line range. Multiple gold regions in one function can therefore receive the "
        "same function-level credit.",
        "",
        "| Model | Frozen recall | Normalized recall | Wrong location | Format mismatch | Bare `N-M` only | Fixed span only |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for alias in ALIASES:
        cell = cells[f"a1|{alias}"]
        lines.append(
            f"| {names[alias]} | {num(cell['frozen_bug_location_recall'])} | "
            f"{num(cell['normalized_location_recall'])} | {cell['wrong_location']} | {cell['format_mismatch']} | "
            f"{cell['bare_range_only_match']} | {cell['fixed_span_only_match']} |"
        )

    lines += [
        "",
        "## A2 frozen errors and manual taxonomy",
        "",
        "Two aliases are at the 100% frozen content-correctness ceiling. Categories below follow the fixed "
        "field/family map and do not alter frozen labels.",
        "",
        "| Model | Frozen correct | Error fields | Frozen labels | Manual categories |",
        "|---|---:|---:|---|---|",
    ]
    for alias in ALIASES:
        cell = cells[f"a2|{alias}"]
        lines.append(
            f"| {names[alias]} | {pct(cell['frozen_content_correct_rate'])} | {cell['error_count']} | "
            f"`{json.dumps(cell['frozen_label_counts'], sort_keys=True)}` | "
            f"`{json.dumps(cell['manual_category_counts'], sort_keys=True)}` |"
        )

    lines += [
        "",
        "## A3 ranking sensitivity",
        "",
        "Valid-only nDCG is at or above the ceiling described in the brief for every alias. The strict view sets "
        "invalid rankings to zero; the deduplicated view keeps first occurrences in the submitted top five and pads "
        "removed duplicates with zero gain.",
        "",
        "| Model | Valid | Frozen | Valid-only | Strict invalid=0 | Deduplicated | Frozen >1 |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for alias in ALIASES:
        cell = cells[f"a3|{alias}"]
        ranking = cell["ranking_ndcg"]
        lines.append(
            f"| {names[alias]} | {cell['ranking_valid']}/30 | {num(ranking['frozen_all_case'])} | "
            f"{num(ranking['valid_ranking_only'])} | {num(ranking['strict_invalid_zero'])} | "
            f"{num(ranking['deduplicated_first5'])} | {cell['frozen_ndcg_over_one']} |"
        )

    lines += [
        "",
        "## A3 grounding sensitivity",
        "",
        "R1 normalizes only the fixed attribute-key vocabulary and retains the all-citations rule. R2 additionally "
        "allows any cited document to support the claim. Values always use the frozen equality rule.",
        "",
        "| Model | Attribute-key coverage | Frozen stored | Frozen recomputed | R1 normalized keys | R2 any citation | Failure reasons |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for alias in ALIASES:
        grounding = cells[f"a3|{alias}"]["grounding"]
        lines.append(
            f"| {names[alias]} | {pct(grounding['attribute_key_coverage'])} | "
            f"{num(grounding['frozen_stored'])} | {num(grounding['frozen_recomputed'])} | "
            f"{num(grounding['relaxed_r1'])} | {num(grounding['relaxed_r2'])} | "
            f"`{json.dumps(grounding['failure_reasons'], sort_keys=True)}` |"
        )

    lines += [
        "",
        "The prompt never specified the allowed claim-attribute vocabulary while the schema accepted arbitrary "
        "strings. Frozen, R1, and R2 grounding values are therefore lower bounds conditional on an unspecified "
        "attribute vocabulary; differences between models must not be interpreted as grounding ability. A future "
        "protocol should provide an enumerated attribute vocabulary in both prompt and schema. Doing so changes "
        "comparability with the existing 270 cells and requires a user decision before a new freeze.",
    ]

    lines += [
        "",
        "## Exploratory paired statistics",
        "",
        "Effects are first model minus second model. Holm correction is within the pre-defined A1 (3), A2 (3), "
        "and A3 (9) families. Non-significance is not evidence of equivalence.",
        "",
        "### Binary primary outcomes",
        "",
        "| Task | Pair | Difference | 95% paired bootstrap CI | Discordant first/second | Exact p | Holm p |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for task in ("a1", "a2"):
        for pair in ("A-B", "A-C", "B-C"):
            row = statistics[task][pair]
            first, second = pair.split("-")
            lines.append(
                f"| {task.upper()} | {names[first]} − {names[second]} | {row['difference']:+.3f} | "
                f"[{row['ci95'][0]:+.3f}, {row['ci95'][1]:+.3f}] | "
                f"{row['first_only']}/{row['second_only']} | {row['p_value']:.4f} | {row['holm_p']:.4f} |"
            )
    lines += [
        "",
        "### A3 paired nDCG",
        "",
        "| View | Pair | Difference | 95% paired bootstrap CI | Nonzero | Wilcoxon p | Holm p |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for view in ("frozen_all_case", "strict_invalid_zero", "deduplicated_first5"):
        for pair in ("A-B", "A-C", "B-C"):
            row = statistics["a3"][view][pair]
            first, second = pair.split("-")
            lines.append(
                f"| `{'frozen_all_case (defective)' if view == 'frozen_all_case' else view}` | "
                f"{names[first]} − {names[second]} | {row['difference']:+.3f} | "
                f"[{row['ci95'][0]:+.3f}, {row['ci95'][1]:+.3f}] | {row['n_nonzero']} | "
                f"{row['p_value']:.4f} | {row['holm_p']:.4f} |"
            )

    lines += [
        "",
        "The project environment did not contain SciPy. The Wilcoxon calculation therefore uses the committed "
        "standard-library implementation of the same two-sided, zero-dropped, tie-corrected normal approximation "
        "without continuity correction; this deviation is explicit in processed metadata.",
        "The A3 Holm family pools nine highly correlated tests across three related ranking views, so its correction "
        "is deliberately conservative.",
        "",
        "## Limits",
        "",
        "- All analyses in this document are post-hoc / exploratory.",
        "- A1 normalized matching is function-level and may credit multiple semantic regions in one function.",
        "- A3 grounding relaxations test formatting and citation aggregation only; they do not validate prose quality.",
        "- The committed `task → topic` attribute alias is a judgment call; no outcome-based vocabulary was added.",
        "- Paired tests have n=30 and ceiling/tie effects; effect intervals matter more than thresholded p-values.",
        "- Frozen results and raw records were not changed.",
        "",
        "## Reproduction",
        "",
        "```bash",
        ".venv/bin/python -m experiments.analyze_independent_v2_posthoc",
        ".venv/bin/python -m pytest -q tests/test_independent_v2_posthoc.py",
        "```",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    result = analyze()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(render_report(result))
    print(json.dumps({
        "label": result["label"],
        "records": sum(len(rows) for rows in result["record_views"].values()),
        "processed": str(OUT.relative_to(REPO)),
        "report": str(REPORT.relative_to(REPO)),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
