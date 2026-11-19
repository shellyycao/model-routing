"""Stage handoff: one policy for same-model AND cross-model transitions.

Policy (HANDOFF_POLICY_VERSION):
- Stage N receives a HandoffPackage built from stage N-1's ACTUAL artifacts: the structured
  output the model returned, the code that was executed, the files the sandbox produced, the
  results verified from those files, and each stage's validation status.
- The package is built by the same function whatever the models on either side are. Nothing in
  it depends on whether the next model equals the previous one (no model-specific summaries,
  no re-prompting, no repair).
- Failed artifacts are passed as-is with status "failed" (no reason text, see below). They are NEVER replaced by
  canonical ground truth. (Under the default terminate policy a failed stage ends the path, so a
  failed package is only built for inspection; it is still saved.)
- NO GROUND-TRUTH LEAKAGE (review M6): validation_status is only "passed" / "failed";
  validator check details (which can contain expected values or reference keys) are never put in
  a package or a prompt. known_limitations carry only model-side observations.
- Every package is written to disk (<run_dir>/<stage>/handoff_in.json) and its size in bytes is
  recorded on the receiving StageRunRecord (handoff_in_path, handoff_size_bytes).
- Long model-written text that is put into the next prompt is capped by bytes (see the caps
  below), identically for every model, so prompt size has a hard upper bound. The full,
  untruncated text is kept in the package / on disk.

Experiment A (independent stage evaluation) builds its packages with `canonical_upstream`, whose
artifacts are the project's canonical reference files (status "passed", so the rendered prompt has
the same form as in Experiment B; the canonical provenance is noted in known_limitations, which is
never rendered into prompts). That is the only place canonical artifacts enter a package.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path

from src.contracts import HandoffPackage, ProjectSpec, StageId

HANDOFF_POLICY_VERSION = "1.0"

# Byte caps for model-written / data text placed into the NEXT prompt (same for every model).
MAX_TEXT_BYTES = 2_000        # cleaning_logic, methods_description, cleaning_summary
MAX_HEAD_BYTES = 4_000        # first lines of a data file
MAX_HEAD_LINES = 12
MAX_STATUS_BYTES = 300        # one validation-status string


def truncate_bytes(text: str, cap: int) -> str:
    """Return `text` cut to at most `cap` UTF-8 bytes (marker included)."""
    data = text.encode("utf-8")
    if len(data) <= cap:
        return text
    marker = f"\n[truncated: {len(data)} bytes in total]"
    keep = max(0, cap - len(marker.encode("utf-8")))
    return data[:keep].decode("utf-8", errors="ignore") + marker


def file_head(path: str | Path, max_lines: int = MAX_HEAD_LINES, cap: int = MAX_HEAD_BYTES) -> tuple[str, int]:
    """(first `max_lines` lines capped to `cap` bytes, total line count). Missing file -> ("", 0)."""
    p = Path(path)
    if not p.is_file():
        return "", 0
    lines: list[str] = []
    total = 0
    with p.open(encoding="utf-8", errors="replace", newline="") as fh:
        for line in fh:
            if total < max_lines:
                lines.append(line.rstrip("\r\n"))
            total += 1
    return truncate_bytes("\n".join(lines), cap), total


@dataclass
class StageArtifacts:
    """What a completed (or failed) stage hands to the next one. Paths are host paths."""

    stage: StageId
    model_alias: str | None
    parsed_output: dict | None                     # model structured output (as dict)
    executed_code: str | None
    files: dict[str, str] = field(default_factory=dict)    # logical name -> host path
    verified_results: dict = field(default_factory=dict)   # sandbox-produced results (never model text)
    validation_status: str = "passed"                      # "passed" | "failed" only
    limitations: list[str] = field(default_factory=list)


def status_string(passed: bool) -> str:
    """Only "passed" / "failed" enters a package (review M6): failure reasons and validator
    details may contain reference values, so they stay in the StageRunRecord on disk only."""
    return "passed" if passed else "failed"


def build_handoff(spec: ProjectSpec, path_id: str, current_stage: StageId,
                  upstream: list[StageArtifacts]) -> HandoffPackage:
    """The single handoff policy. `upstream` = artifacts of every completed stage, in order."""
    source_files: list[str] = []
    if current_stage == StageId.CLEANING or not upstream:
        # The raw file is the only source of the first stage.
        source_files.append("raw:" + spec.raw_data_file)
    for a in upstream:
        source_files += [str(p) for p in a.files.values()]
    limitations = [f"{a.stage.value}: {l}" for a in upstream for l in a.limitations]
    return HandoffPackage(
        project_id=spec.project_id,
        path_id=path_id,
        original_objective=spec.objective,
        current_stage=current_stage,
        completed_stages=[a.stage for a in upstream],
        stage_outputs={a.stage.value: (a.parsed_output or {}) for a in upstream},
        source_files=source_files,
        executed_code={a.stage.value: a.executed_code for a in upstream if a.executed_code is not None},
        verified_results={a.stage.value: a.verified_results for a in upstream},
        validation_status={a.stage.value: a.validation_status for a in upstream},
        known_limitations=limitations,
    )


def save_handoff(pkg: HandoffPackage, path: str | Path) -> int:
    """Write the package as JSON; return its size_bytes()."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(json.loads(pkg.model_dump_json()), indent=2, ensure_ascii=False), encoding="utf-8")
    return pkg.size_bytes()


def build_and_save(spec: ProjectSpec, path_id: str, current_stage: StageId, upstream: list[StageArtifacts],
                   path: str | Path) -> tuple[HandoffPackage, int, float]:
    """-> (package, size_bytes, handoff_ms)."""
    t0 = time.perf_counter()
    pkg = build_handoff(spec, path_id, current_stage, upstream)
    size = save_handoff(pkg, path)
    return pkg, size, (time.perf_counter() - t0) * 1000


def canonical_upstream(spec: ProjectSpec, project_dir: str | Path, stage: StageId) -> list[StageArtifacts]:
    """Experiment A ONLY: upstream artifacts made from the project's canonical reference files."""
    pdir = Path(project_dir)
    note = "canonical reference artifact (trusted code), Experiment A independent stage evaluation"
    out: list[StageArtifacts] = []
    if stage in (StageId.ANALYSIS, StageId.REPORTING):
        out.append(StageArtifacts(
            stage=StageId.CLEANING, model_alias=None,
            parsed_output={"cleaning_logic": "Canonical reference cleaning: the cleaning requirements were "
                                             "applied by trusted reference code."},
            executed_code=None,
            files={"cleaned_csv": str(pdir / spec.canonical_cleaned_file)},
            verified_results={}, validation_status="passed", limitations=[note]))
    if stage == StageId.REPORTING:
        findings = json.loads((pdir / spec.canonical_findings_file).read_text(encoding="utf-8"))
        out.append(StageArtifacts(
            stage=StageId.ANALYSIS, model_alias=None,
            parsed_output={"methods_description": "Canonical reference analysis: the analysis questions were "
                                                  "answered by trusted reference code."},
            executed_code=None,
            files={"findings": str(pdir / spec.canonical_findings_file)},
            verified_results={"findings": findings}, validation_status="passed", limitations=[note]))
    return out
