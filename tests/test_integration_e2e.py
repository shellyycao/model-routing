"""Lead-owned integration test: one complete three-stage workflow through the REAL pieces.

Real: DockerExecutor (verified sandbox image), SandboxGate (results/verification/sandbox_verification.json),
validators, handoff, orchestrator, storage. Fake: only the LLM (SYNTHETIC_FIXTURE responses that return
the Benchmark's trusted reference scripts, optionally with an injected bug). No AWS calls.
Skipped when the Docker daemon / verified image is unavailable.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from src.contracts import StageStatus
from src.storage import RunStore
from src.workflow.executor import DockerExecutor
from src.workflow.orchestrator import WorkflowOrchestrator
from src.workflow.stages import SandboxGate
from tests.fixtures.workflow.fakes import FakeBedrockRuntime, make_client

REPO = Path(__file__).resolve().parents[1]
EXP = "expB_paths"


_ok, _reason = DockerExecutor().availability()
pytestmark = pytest.mark.skipif(not _ok, reason=f"real sandbox unavailable: {_reason}")


def _orch(tmp_path, behaviours=None):
    client = make_client(tmp_path, FakeBedrockRuntime(behaviours))
    store = RunStore(EXP, root=tmp_path / "results")
    return WorkflowOrchestrator(client, DockerExecutor(), store, gate=SandboxGate(),
                                failure_policy="continue_with_actual_artifact")


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def test_e2e_three_stage_path_real_sandbox(tmp_path):
    rec = _orch(tmp_path).run_path("retail_sales", "A-B-C", EXP, 0)
    assert [s.status for s in rec.stages] == [StageStatus.PASSED] * 3, [s.failure_detail for s in rec.stages]
    assert rec.feasibility.outcome == "feasible"
    verified = __import__("json").loads(
        (REPO / "results/verification/sandbox_verification.json").read_text())["image_id"]
    for s in rec.stages[:2]:
        assert s.execution is not None and s.execution.sandbox_image == verified   # really ran in the verified image
    # Stage 2 consumed stage 1's actual output (hash chain).
    cleaned_out = set(rec.stages[0].output_artifact_hashes.values())
    assert cleaned_out & set(rec.stages[1].input_artifact_hashes.values())


@pytest.fixture
def bug_in_code(monkeypatch):
    """The shared fake passes bugs as a header only FixtureExecutor reads; a real container would ignore it.
    Here the bug is put INTO the generated code so the sandbox really executes the buggy cleaning."""
    import tests.fixtures.workflow.fakes as fakes
    orig = fakes.solution_code

    def real_bug(project_id, stage, bug=None):
        code = orig(project_id, stage, None)
        return (f"import sys\nsys.argv = [sys.argv[0], {bug!r}]\n" + code) if bug else code
    monkeypatch.setattr(fakes, "solution_code", real_bug)


def test_e2e_imperfect_upstream_reaches_downstream_real_sandbox(tmp_path, bug_in_code):
    rec = _orch(tmp_path, {("B", "cleaning"): "bug:no_dedup"}).run_path("retail_sales", "B-A-C", EXP, 0)
    cl, an, rp = rec.stages
    assert cl.status == StageStatus.FAILED and cl.structural_ok is True        # semantically wrong, consumable
    assert an.status != StageStatus.BLOCKED_BY_INVALID_ARTIFACT and an.invocation_ids   # analysis actually ran
    canonical = _sha(REPO / "datasets/projects/retail_sales/canonical/cleaned.csv")
    assert canonical not in an.input_artifact_hashes.values()                  # never swapped for ground truth
    assert rec.feasibility.outcome == "infeasible"                             # strict gate still fails
    sev = rec.propagation.upstream_error_severity["analysis"]
    assert max(sev.values()) > 0
    assert rp.status in (StageStatus.PASSED, StageStatus.FAILED)               # reporting ran on actual findings
