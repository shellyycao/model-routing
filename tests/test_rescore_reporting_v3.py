"""The offline v3 rescore is additive and leaves frozen raw evidence untouched."""

from pathlib import Path

from experiments.rescore_reporting_v3 import rescore
from src.bedrock.provenance import hash_file


def test_saved_outputs_rescore_side_by_side_without_raw_mutation():
    records = Path("results/raw/workflow_runs/expB_paths.jsonl")
    sample = Path("results/raw/runs/expB_paths-4308de5346884de6/reporting/output/report.json")
    before = (hash_file(records), hash_file(sample))
    payload = rescore(records, Path("results/raw"), "retail_sales",
                      Path("datasets/projects/retail_sales"))
    after = (hash_file(records), hash_file(sample))
    assert before == after
    assert payload["raw_outputs_modified"] is False
    assert payload["source_records_sha256"] == before[0]
    assert payload["summary"] == {
        "reports_rescored": 10,
        "v2_ground_truth_passed": 0,
        "v3_ground_truth_passed": 7,
        "transitions": {"v2_False_to_v3_False": 3, "v2_False_to_v3_True": 7},
    }
    assert all(row["v2_ground_truth"]["validator_version"] == "2.0" for row in payload["records"])
    assert all(row["v3_ground_truth"]["validator_version"] == "3.0-post-freeze"
               for row in payload["records"])
