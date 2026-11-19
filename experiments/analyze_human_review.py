"""Validate, unblind, and summarize the completed independent-v1 human review.

The completed worksheet is treated strictly as data.  It is copied into the
repository as a locked review artifact; no judgment is edited or inferred.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
REVIEW = REPO / "results/review"
PROCESSED = REPO / "results/processed/independent/human_review_results.json"
REPORT = REPO / "results/reports/human_review_results.md"

HUMAN_FIELDS = [
    "human_overall_judgment",
    "human_content_correct",
    "human_schema_compliant",
    "human_operationally_usable",
    "human_ranking_quality_0_to_3",
    "human_grounding_quality_0_to_3",
    "human_citation_accuracy_0_to_3",
    "error_classification",
    "reviewer_notes",
]
ALLOWED = {
    "human_overall_judgment": {"correct", "mostly_correct", "incorrect", "not_judgeable"},
    "human_content_correct": {"yes", "partial", "no", "NA"},
    "human_schema_compliant": {"yes", "no", "NA"},
    "human_operationally_usable": {"yes", "no", "NA"},
    "human_ranking_quality_0_to_3": {"0", "1", "2", "3", "NA"},
    "human_grounding_quality_0_to_3": {"0", "1", "2", "3", "NA"},
    "human_citation_accuracy_0_to_3": {"0", "1", "2", "3", "NA"},
}


def _read_csv(path: Path) -> list[dict]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _raw_records() -> dict[str, dict]:
    output = {}
    for path in sorted((REPO / "results/raw/independent").glob("*.jsonl")):
        for line in path.read_text().splitlines():
            if line.strip():
                record = json.loads(line)
                output[record["run_id"]] = record
    return output


def _count(rows: list[dict], key: str) -> dict[str, int]:
    return dict(sorted(Counter(row[key] for row in rows).items()))


def _ratio(matches: list[bool]) -> dict:
    return {"matches": sum(matches), "n": len(matches), "rate": sum(matches) / len(matches) if matches else None}


def _md(value) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--completed", required=True)
    args = parser.parse_args(argv)
    source = Path(args.completed).resolve()
    completed = _read_csv(source)
    key_rows = _read_csv(REVIEW / "human_review_key.csv")
    manifest = json.loads((REVIEW / "human_review_manifest.json").read_text())
    if len(completed) != manifest["sample_count"]:
        raise SystemExit(f"expected {manifest['sample_count']} review rows, got {len(completed)}")
    expected_ids = {row["anonymous_sample_id"] for row in key_rows}
    actual_ids = [row["anonymous_sample_id"] for row in completed]
    if len(actual_ids) != len(set(actual_ids)) or set(actual_ids) != expected_ids:
        raise SystemExit("completed worksheet IDs are duplicated or do not match the blinded key")
    for row in completed:
        for field in HUMAN_FIELDS:
            if not (row.get(field) or "").strip():
                raise SystemExit(f"blank required review field: {row['anonymous_sample_id']} {field}")
        for field, allowed in ALLOWED.items():
            if row[field].strip() not in allowed:
                raise SystemExit(f"invalid value: {row['anonymous_sample_id']} {field}={row[field]!r}")

    completed_by_id = {row["anonymous_sample_id"]: row for row in completed}
    records = _raw_records()
    audit = json.loads((REPO / "results/processed/independent/audit_v1.json").read_text())
    recovered = {row["run_id"]: row for row in audit["a2_unwrapped_recovery"]}
    v11 = {row["run_id"]: row["grounding_v1_1"] for row in audit["a3_grounding_reclassification"]}
    joined = []
    for key in key_rows:
        human = completed_by_id[key["anonymous_sample_id"]]
        record = records[key["run_id"]]
        joined.append({
            "anonymous_sample_id": key["anonymous_sample_id"],
            "task": key["task"],
            "case_id": key["case_id"],
            "model_alias": key["model_alias"],
            "model_name": key["model_name"],
            "run_id": key["run_id"],
            "automatic": {
                "status": record["status"],
                "failure_type": record.get("failure_type"),
                "parse_ok": record["parse_ok"],
                "scores": record.get("scores") or {},
                "a2_recovered_content_correct": recovered.get(record["run_id"], {}).get("content_correct"),
                "a3_grounding_v1_1": v11.get(record["run_id"]),
            },
            "human": {field: human[field].strip() for field in HUMAN_FIELDS},
        })

    task_rows = {task: [row for row in joined if row["task"] == task] for task in ("a1", "a2", "a3")}
    a1_functional = []
    for row in task_rows["a1"]:
        auto = bool(row["automatic"]["scores"].get("functional_correct"))
        human = row["human"]["human_content_correct"] == "yes"
        a1_functional.append(auto == human)

    a2_strict, a2_recovered, a2_schema, a2_operational = [], [], [], []
    for row in task_rows["a2"]:
        scores = row["automatic"]["scores"]
        auto_strict = bool(scores.get("all_fields_correct"))
        human_content = row["human"]["human_content_correct"] == "yes"
        recovered_content = row["automatic"]["a2_recovered_content_correct"]
        auto_recovered = auto_strict if recovered_content is None else bool(recovered_content)
        a2_strict.append(auto_strict == human_content)
        a2_recovered.append(auto_recovered == human_content)
        a2_schema.append(bool(row["automatic"]["parse_ok"]) == (row["human"]["human_schema_compliant"] == "yes"))
        a2_operational.append(bool(row["automatic"]["parse_ok"]) == (row["human"]["human_operationally_usable"] == "yes"))

    a3_operational = [
        (row["automatic"]["status"] == "passed") == (row["human"]["human_operationally_usable"] == "yes")
        for row in task_rows["a3"]
    ]
    a3_pairs = []
    for row in task_rows["a3"]:
        scores = row["automatic"]["scores"]
        a3_pairs.append({
            "anonymous_sample_id": row["anonymous_sample_id"],
            "model_alias": row["model_alias"],
            "case_id": row["case_id"],
            "automatic_status": row["automatic"]["status"],
            "ndcg_at_5": scores.get("ndcg_at_5"),
            "human_ranking_0_to_3": row["human"]["human_ranking_quality_0_to_3"],
            "grounding_v1": scores.get("grounding_accuracy"),
            "grounding_v1_1": row["automatic"]["a3_grounding_v1_1"],
            "human_grounding_0_to_3": row["human"]["human_grounding_quality_0_to_3"],
            "citation_consistent_structural": scores.get("citation_consistent"),
            "human_citation_0_to_3": row["human"]["human_citation_accuracy_0_to_3"],
        })

    parsed_a3 = [pair for pair in a3_pairs if pair["citation_consistent_structural"] is not None]
    summary = {
        "sample_count": len(joined),
        "sampling_warning": "Purposive stratified spot-check; not an unbiased performance estimate.",
        "overall_judgments": _count([row["human"] for row in joined], "human_overall_judgment"),
        "by_task": {
            task: {
                "n": len(rows),
                "overall_judgments": _count([row["human"] for row in rows], "human_overall_judgment"),
                "error_classes": _count([row["human"] for row in rows], "error_classification"),
            }
            for task, rows in task_rows.items()
        },
        "agreement": {
            "a1_functional_correctness": _ratio(a1_functional),
            "a2_strict_content_correctness": _ratio(a2_strict),
            "a2_recovered_content_correctness": _ratio(a2_recovered),
            "a2_schema_compliance": _ratio(a2_schema),
            "a2_operational_usability": _ratio(a2_operational),
            "a3_operational_usability": _ratio(a3_operational),
            "a3_structural_citation_consistent_count": sum(bool(pair["citation_consistent_structural"]) for pair in parsed_a3),
            "a3_parsed_count": len(parsed_a3),
            "a3_human_perfect_citation_count": sum(pair["human_citation_0_to_3"] == "3" for pair in parsed_a3),
        },
        "a3_pairs": a3_pairs,
        "confirmed_findings": [
            "A1 functional tests agreed with all six reviewed human judgments.",
            "A1 a1_09 localization is a false reject: the mutation is in rank_key, while the scorer requires the top_k function name.",
            "A2 strict content disagreed on the wrapper-only failure; recovered content and schema/operational judgments each agreed on all six reviewed items.",
            "A3 nDCG can remain high despite a human-important fifth-rank error, and perfect nDCG still permits summary framing or grounding defects.",
            "A3 frozen v1 grounding false-rejects faithful paraphrases, while structured-claim grounding can false-accept unsupported prose not represented in claims.",
            "A3 citation_consistent checks citation structure, not attribution accuracy: five parsed samples passed structurally, but only two received a perfect human citation score.",
        ],
    }
    REVIEW.mkdir(parents=True, exist_ok=True)
    completed_path = REVIEW / "human_review_completed.csv"
    _write_csv(completed_path, completed)
    result = {
        "mode": "completed blinded human spot-check, unblinded only after judgments were locked",
        "source_file_name": source.name,
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "normalized_completed_sha256": hashlib.sha256(completed_path.read_bytes()).hexdigest(),
        "manifest_worksheet_sha256": manifest["worksheet_sha256"],
        "completed_rows": len(completed),
        "validation": {"all_ids_match": True, "all_required_fields_complete": True, "all_values_allowed": True},
        "summary": summary,
        "joined_rows": joined,
    }
    PROCESSED.parent.mkdir(parents=True, exist_ok=True)
    PROCESSED.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    lines = [
        "# Human Spot-check Results",
        "",
        "**Status:** completed and unblinded after all 18 judgments were locked",
        "",
        "**Scope:** purposive, stratified review of two outputs per task-model cell; descriptive validation, not a performance estimate",
        "",
        "## Completion and integrity",
        "",
        f"- Completed rows: {len(completed)}/18.",
        "- Anonymous IDs match the sampling key exactly.",
        "- Every required human field is populated with a protocol-allowed value.",
        f"- Imported completed-file SHA-256: `{result['source_sha256']}`.",
        "- Model identities and automatic scores were joined only after completion.",
        "",
        "## Human judgments",
        "",
        "| Task | n | Correct | Mostly correct | Incorrect |",
        "|---|---:|---:|---:|---:|",
    ]
    for task in ("a1", "a2", "a3"):
        counts = summary["by_task"][task]["overall_judgments"]
        lines.append(f"| {task.upper()} | 6 | {counts.get('correct', 0)} | {counts.get('mostly_correct', 0)} | {counts.get('incorrect', 0)} |")
    counts = summary["overall_judgments"]
    lines += [
        f"| **Total** | **18** | **{counts.get('correct', 0)}** | **{counts.get('mostly_correct', 0)}** | **{counts.get('incorrect', 0)}** |",
        "",
        "The sample intentionally over-represents failures, borderline cases, and scorer disagreements. These counts must not be reported as model accuracy rates.",
        "",
        "## Automatic–human agreement",
        "",
        "| Comparison | Agreement | Interpretation |",
        "|---|---:|---|",
        f"| A1 functional correctness | {summary['agreement']['a1_functional_correctness']['matches']}/6 | Hidden-test functional labels agreed with the human judgment. |",
        f"| A2 strict content correctness | {summary['agreement']['a2_strict_content_correctness']['matches']}/6 | The mismatch is a content-correct response rejected for its missing wrapper. |",
        f"| A2 recovered content correctness | {summary['agreement']['a2_recovered_content_correctness']['matches']}/6 | Separating recoverable content resolves the disagreement. |",
        f"| A2 schema compliance | {summary['agreement']['a2_schema_compliance']['matches']}/6 | Wrapper/parse compliance agreed. |",
        f"| A2 operational usability | {summary['agreement']['a2_operational_usability']['matches']}/6 | Immediate pipeline usability agreed. |",
        f"| A3 operational usability | {summary['agreement']['a3_operational_usability']['matches']}/6 | One four-ID parsed response was human-usable but failed the exact-five automatic rule. |",
        "",
        "## A3 detailed comparison",
        "",
        "| Sample | Model | Case | Status | nDCG@5 | Human ranking | Grounding v1 | Grounding v1.1 | Human grounding | Structural citation | Human citation |",
        "|---|---|---|---|---:|---:|---:|---:|---:|---|---:|",
    ]
    for pair in a3_pairs:
        lines.append(
            f"| {pair['anonymous_sample_id']} | {pair['model_alias']} | {pair['case_id']} | {pair['automatic_status']} | "
            f"{_md(pair['ndcg_at_5'])} | {pair['human_ranking_0_to_3']} | {_md(pair['grounding_v1'])} | "
            f"{_md(pair['grounding_v1_1'])} | {pair['human_grounding_0_to_3']} | "
            f"{_md(pair['citation_consistent_structural'])} | {pair['human_citation_0_to_3']} |"
        )
    lines += [
        "",
        "## Confirmed and new findings",
        "",
        "1. **A1 functional scoring is credible on the reviewed items, but localization is not.** `a1_09_top_k` correctly identifies `rank_key`, the actual mutated helper, while the scorer searches only for `top_k` and marks localization false.",
        "2. **A2 must retain separate content and operational scores.** The reviewer confirmed the bare-object response is fully content-correct but not schema-compliant or directly usable.",
        "3. **A3 ranking metrics understate some qualitative errors.** nDCG 0.952 can still omit the required fifth relevant study, and nDCG 1.0 does not guarantee that the synthesis frames a grade-1 paper appropriately.",
        "4. **Grounding needs both accepted paraphrases and prose coverage.** v1 rejects faithful abstract wording; structured-claim scoring can also miss unsupported prose when the response omits that prose assertion from its claim list.",
        f"5. **Citation structure is not citation accuracy.** All {len(parsed_a3)} parsed reviewed A3 outputs passed `citation_consistent`, but only {summary['agreement']['a3_human_perfect_citation_count']}/{len(parsed_a3)} received a perfect human citation score.",
        "",
        "## Consequences",
        "",
        "- Frozen v1 scores remain unchanged and primary.",
        "- Human results validate the A2 post-hoc content/schema decomposition and A3 v1.1 paraphrase repair, while identifying additional A1-localization and A3-prose/citation limitations.",
        "- These results should inform v2 scorer design before freeze, without using future evaluated-model outputs.",
        "- This v1 spot-check does not adjudicate the candidate v2 A3 relevance labels; that remains a separate pre-freeze task.",
        "",
        "Reproduce with:",
        "",
        "```bash",
        ".venv/bin/python -m experiments.analyze_human_review --completed <completed_worksheet.csv>",
        "```",
    ]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n")
    print(json.dumps({
        "completed_copy": str(completed_path.relative_to(REPO)),
        "processed": str(PROCESSED.relative_to(REPO)),
        "report": str(REPORT.relative_to(REPO)),
        "rows": len(completed),
        "overall": summary["overall_judgments"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
