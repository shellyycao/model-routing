# Sandbox isolation verification (2026-11-18)

- **Image:** `model-routing-xai-sandbox:1.0`, ID `sha256:4bf3a80b1190efe621b87440374a36cd4a6e1639bdff6f872a530c7f63f698b1`.
- **Built from:** `sandbox/Dockerfile`, base `python:3.12.8-slim-bookworm`, numpy 2.2.6, pandas 2.2.3.
- **Host:** Docker Desktop 28.3.3.
- **Command:** `.venv/bin/python -m pytest -v -rs tests/test_executor.py`.

## Results

**First run: 15 passed, 1 failed** (`test_isolation_no_network`).
- The test asserted that the container's only network interface was `lo`. Docker Desktop's LinuxKit kernel creates fallback tunnel devices in every network namespace (`tunl0`, `gre0`, `gretap0`, `erspan0`, `ip_vti0`, `ip6_vti0`, `sit0`, `ip6tnl0`, `ip6gre0`). They appear even under `--network none`.
- Investigation under `--network none` with the sandbox's flags:
  - every device except `lo` is DOWN (`IFF_UP` not set);
  - there are no IPv4 or IPv6 routes;
  - outbound connections and DNS fail.
- **Conclusion:** the network control works; the assertion did not match it.

**Correction, made by the lead in a test file the Benchmark agent owns** (that agent had finished, so there was no concurrent edit). The test now asserts the actual control:
1. no connection or DNS;
2. `lo` is the only interface that is up;
3. no routes;
4. the code cannot raise an interface (`SIOCSIFFLAGS` is denied, since all capabilities are dropped).

**Negative control:** the same checks with networking enabled (default bridge) report `eth0` up, 2 routes, and a successful connection. The corrected test would therefore fail if the network were reachable.

**Second run: 16 passed, 0 failed, 0 skipped.**

All isolation controls are verified for this image ID: no network, no AWS environment or credentials, no writes outside the output directory, read-only inputs, non-root with no privilege escalation, memory limit, timeout kill, runtime-error mapping, and the end-to-end reference solutions for all 3 projects.

Recorded in `results/raw/sandbox_verification.json`. The Workflow orchestrator's sandbox gate reads this file. Rebuilding the image changes its ID and requires re-verification.

## Not covered
- **Base image digest:** BuildKit doesn't keep the base as a separate image, so its digest wasn't recorded. The built image ID is recorded instead.
- **Other hosts:** Linux-host behaviour (output directory permissions) wasn't tested.
- **Escape attempts:** kernel- or VM-level escapes are outside the scope of these tests.
