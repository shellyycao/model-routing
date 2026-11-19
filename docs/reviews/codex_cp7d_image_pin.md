# Codex CP7d — immutable sandbox image pin

## Execution amendment

On 2026-11-19, before any main-run call, Docker Desktop was found to intermittently reject the
short image reference `model-routing-xai-sandbox:1.0` while the fully qualified reference and image
ID remained available. This is an execution-layer short-name resolution failure in Docker
Desktop's containerd store. The scientific protocol—data, prompts, models, parameters, ordering,
validators, retries, and $100 cap—is unchanged.

## Implementation and tests

The price-matched workflow runner now constructs `DockerExecutor` with the verified immutable ID
`sha256:88988a15503bdb96538c3dd62244a79879d5c7848397db18b1267ccfd0a9727a`.
Availability inspection, every sandbox `docker run`, and the restricted image lease therefore use
the same reference. A missing ID fails before Bedrock client construction with an explicit
no-short-name-fallback error. The shared `DEFAULT_IMAGE` and shared sandbox gate were not changed;
a runner-private gate adapter preserves the verification record's optional human-readable tag
while delegating availability to the actual ID-pinned executor.

Mocked offline tests cover the ID used by availability/run/lease, successful verified construction,
missing-ID failure, no Bedrock construction on failure, and rejection of the old execution tag.
The full suite passed: **520 passed, 23 skipped**. No model or network calls were made.

## Freeze handoff

The regenerated manifest retains status `main_frozen_paid_execution_approved`, the user's exact
approval wording, `maxTokens=16384`, Kimi's temperature omission, and the shared $100 cap. It adds
the dated execution-only amendment, active sandbox-verification hash, proof of zero main task
records/invocations before the amendment, and required tag `price-matched-workflow-main-v1.1`.
The old `price-matched-workflow-main-v1` tag must remain and does not authorize this runner. Claude
should commit the amendment, create the new tag, verify the manifest at that tag, and only then use
the unchanged CP7c execution commands.
