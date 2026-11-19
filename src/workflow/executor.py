"""Isolated execution of untrusted model-generated Python code (implements src.contracts.Executor).

DockerExecutor runs each script in a fresh container of the sandbox image (sandbox/Dockerfile):

  --network none                       no network at all
  --read-only + --tmpfs /tmp           root filesystem read-only; scratch space in a small tmpfs
  --memory/--memory-swap, --cpus,      resource limits (memory-swap == memory -> no swap)
  --pids-limit
  --user 10001:10001                   non-root
  --cap-drop ALL, --security-opt no-new-privileges, --ipc none
  inputs  -> /sandbox/input/<name>:ro  each input file mounted individually, read-only
  code    -> /sandbox/code/main.py:ro  read-only
  output_dir -> /sandbox/output:rw     the ONLY writable bind mount
  environment                          only INPUT_DIR / OUTPUT_DIR are set (-e NAME=value). Host env
                                       is never forwarded; the docker CLI itself is started with a
                                       minimal allow-listed env (no AWS_* or other secrets), so even
                                       a mistaken pass-through could not leak credentials. No home
                                       directory or ~/.aws is ever mounted.
  wall-clock timeout                   the container is killed and removed -> TIMEOUT

If Docker or the sandbox image is unavailable the result is SANDBOX_UNAVAILABLE. There is NO
fallback that runs code on the host.

Status mapping: exit 0 -> SUCCESS; timeout -> TIMEOUT; OOM-killed or other non-zero exit ->
RUNTIME_ERROR; docker-level failure (exit 125, daemon/image missing) -> SANDBOX_UNAVAILABLE;
symlinks/special files or oversized output in output_dir -> SECURITY_VIOLATION / INVALID_OUTPUT.
Semantic output checks (TEST_FAILURE, INVALID_OUTPUT for wrong content) belong to the validators.
"""

from __future__ import annotations

import os
import re
import shutil
import stat
import subprocess
import tempfile
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from src.contracts import ExecutionResult, ExecutionStatus, ResourceLimits

DEFAULT_IMAGE = "model-routing-xai-sandbox:1.0"
SANDBOX_UID = "10001:10001"
IN_DIR, CODE_DIR, OUT_DIR = "/sandbox/input", "/sandbox/code", "/sandbox/output"
_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
# Only these host variables reach the docker CLI process (needed to locate the daemon).
_CLI_ENV_ALLOW = ("PATH", "HOME", "DOCKER_HOST", "DOCKER_CONTEXT", "DOCKER_CONFIG", "DOCKER_CERT_PATH",
                  "DOCKER_TLS_VERIFY", "TMPDIR", "LANG", "LC_ALL")
MAX_STREAM_CHARS = 64_000
IMAGE_LEASE_LABEL = "model-routing-xai.image-lease=true"


def docker_cli_env() -> dict[str, str]:
    env = {k: os.environ[k] for k in _CLI_ENV_ALLOW if k in os.environ}
    return {k: v for k, v in env.items() if not k.upper().startswith("AWS")}


def _truncate(s: str) -> str:
    return s if len(s) <= MAX_STREAM_CHARS else s[:MAX_STREAM_CHARS] + f"\n[truncated {len(s) - MAX_STREAM_CHARS} chars]"


def _bind(src: Path, target: str, readonly: bool) -> str:
    """--mount spec. Paths containing ',' or '"' are rejected (they could inject mount options)."""
    path = str(Path(src).resolve())
    if "," in path or '"' in path or "\n" in path:
        raise ValueError(f"unsafe characters in host path: {path!r}")
    return f"type=bind,source={path},target={target}" + (",readonly" if readonly else "")


class DockerExecutor:
    def __init__(self, image: str = DEFAULT_IMAGE, docker_bin: str = "docker", pids_limit: int = 128,
                 tmpfs_mb: int = 64, max_output_mb: int = 200, daemon_check_timeout_s: float = 10.0):
        self.image = image
        self.docker_bin = docker_bin
        self.pids_limit = pids_limit
        self.tmpfs_mb = tmpfs_mb
        self.max_output_bytes = max_output_mb * 1024 * 1024
        self.daemon_check_timeout_s = daemon_check_timeout_s

    # ------------------------------------------------------------------ docker helpers
    def _docker(self, *args: str, timeout: float = 30.0) -> subprocess.CompletedProcess:
        return subprocess.run([self.docker_bin, *args], capture_output=True, text=True, timeout=timeout,
                              env=docker_cli_env(), stdin=subprocess.DEVNULL)

    def availability(self) -> tuple[bool, str]:
        """(available, reason). Checks the CLI, the daemon and the sandbox image."""
        if shutil.which(self.docker_bin) is None and not Path(self.docker_bin).is_file():
            return False, f"docker CLI not found ({self.docker_bin})"
        try:
            info = self._docker("info", "--format", "{{.ServerVersion}}", timeout=self.daemon_check_timeout_s)
        except (OSError, subprocess.TimeoutExpired) as e:
            return False, f"docker daemon check failed: {e}"
        if info.returncode != 0:
            return False, f"docker daemon unavailable: {(info.stderr or info.stdout).strip()[:300]}"
        img = self._docker("image", "inspect", "--format", "{{.Id}}", self.image)
        if img.returncode != 0:
            return False, f"sandbox image {self.image} not found; build it with: docker build -t {self.image} sandbox/"
        return True, img.stdout.strip()

    def build_run_command(self, container_name: str, code_path: Path, inputs: dict[str, str],
                          output_dir: Path, limits: ResourceLimits) -> list[str]:
        """The exact `docker run` argv (pure function; unit-tested without a daemon)."""
        if limits.network:
            raise ValueError("network access is never allowed for model-generated code")
        mem = f"{int(limits.memory_mb)}m"
        cmd = [self.docker_bin, "run", "--name", container_name,
               "--network", "none",
               "--read-only",
               "--tmpfs", f"/tmp:rw,noexec,nosuid,nodev,size={self.tmpfs_mb}m",
               "--memory", mem, "--memory-swap", mem,
               "--cpus", f"{float(limits.cpus):g}",
               "--pids-limit", str(self.pids_limit),
               "--user", SANDBOX_UID,
               "--cap-drop", "ALL",
               "--security-opt", "no-new-privileges",
               "--ipc", "none",
               "--workdir", OUT_DIR,
               "--env", f"INPUT_DIR={IN_DIR}", "--env", f"OUTPUT_DIR={OUT_DIR}",
               "--mount", _bind(code_path, f"{CODE_DIR}/main.py", readonly=True)]
        for name, host in sorted(inputs.items()):
            if not _NAME_RE.match(name) or name in (".", ".."):
                raise ValueError(f"invalid in-sandbox input name: {name!r}")
            hp = Path(host).resolve()
            if not hp.exists():
                raise FileNotFoundError(f"input {name!r} not found: {host}")
            cmd += ["--mount", _bind(hp, f"{IN_DIR}/{name}", readonly=True)]
        cmd += ["--mount", _bind(output_dir, OUT_DIR, readonly=False), self.image, f"{CODE_DIR}/main.py"]
        return cmd

    def build_image_lease_command(self, container_name: str) -> list[str]:
        """Create a tiny, isolated holder container so Docker pruning cannot remove the image.

        A running container references the exact local image behind ``self.image``. Docker's normal
        image-prune operations will not delete an image used by a container. The holder has no
        network, mounts, credentials or writable root filesystem and executes only ``sleep``.
        """
        return [
            self.docker_bin, "run", "--detach", "--pull", "never", "--name", container_name,
            "--label", IMAGE_LEASE_LABEL,
            "--network", "none", "--read-only", "--tmpfs", "/tmp:rw,noexec,nosuid,nodev,size=1m",
            "--memory", "32m", "--memory-swap", "32m", "--cpus", "0.1", "--pids-limit", "16",
            "--user", SANDBOX_UID, "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
            "--ipc", "none", "--restart", "no", "--entrypoint", "/bin/sleep",
            self.image, "infinity",
        ]

    @contextmanager
    def image_lease(self, expected_image_id: str) -> Iterator[str]:
        """Pin the verified image for a multi-call run and remove the holder on clean exit.

        This is deliberately not an auto-build or auto-restore mechanism: a missing or changed image
        still fails closed and must be rebuilt, re-tested and re-recorded by the operator.
        """
        ok, info = self.availability()
        if not ok:
            raise RuntimeError(f"cannot acquire sandbox image lease: {info}")
        if info != expected_image_id:
            raise RuntimeError(
                f"cannot acquire sandbox image lease: local image ID {info!r} != verified {expected_image_id!r}")
        name = f"mrx-sbx-lease-{os.getpid()}-{uuid.uuid4().hex[:8]}"
        cmd = self.build_image_lease_command(name)
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30,
                              env=docker_cli_env(), stdin=subprocess.DEVNULL)
        if proc.returncode != 0:
            raise RuntimeError(f"cannot acquire sandbox image lease: {(proc.stderr or proc.stdout).strip()[:500]}")
        try:
            # Re-check the tag after the holder starts; no paid call should begin if it moved.
            ok, info = self.availability()
            if not ok or info != expected_image_id:
                raise RuntimeError(
                    f"sandbox image changed while acquiring lease: {info!r} (expected {expected_image_id!r})")
            yield name
        finally:
            self._remove(name)

    # ------------------------------------------------------------------ main entry point
    def execute(self, code: str, inputs: dict[str, str], output_dir: str,
                limits: ResourceLimits | None = None) -> ExecutionResult:
        limits = limits or ResourceLimits()
        ok, info = self.availability()
        if not ok:
            return ExecutionResult(status=ExecutionStatus.SANDBOX_UNAVAILABLE, stderr=info)
        image_id = info
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        # The container user (uid 10001) must be able to write here on Linux hosts.
        out.chmod(0o777)
        name = f"mrx-sbx-{uuid.uuid4().hex[:16]}"
        with tempfile.TemporaryDirectory(prefix="mrx-code-") as tmp:
            code_path = Path(tmp) / "main.py"
            code_path.write_text(code, encoding="utf-8")
            code_path.chmod(0o444)
            Path(tmp).chmod(0o755)
            try:
                cmd = self.build_run_command(name, code_path, inputs, out, limits)
            except (ValueError, FileNotFoundError) as e:
                return ExecutionResult(status=ExecutionStatus.SECURITY_VIOLATION if isinstance(e, ValueError)
                                       else ExecutionStatus.RUNTIME_ERROR, stderr=f"[sandbox] {e}",
                                       sandbox_image=image_id)
            t0 = time.monotonic()
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.DEVNULL,
                                    text=True, env=docker_cli_env())
            try:
                stdout, stderr = proc.communicate(timeout=limits.timeout_s)
                timed_out = False
            except subprocess.TimeoutExpired:
                timed_out = True
                self._kill(name)
                proc.kill()
                stdout, stderr = proc.communicate()
            runtime_ms = (time.monotonic() - t0) * 1000
            oom = False
            if not timed_out:
                insp = self._docker("inspect", "--format", "{{.State.OOMKilled}}", name)
                oom = insp.returncode == 0 and insp.stdout.strip() == "true"
            self._remove(name)

        base = dict(exit_code=None if timed_out else proc.returncode, stdout=_truncate(stdout or ""),
                    stderr=_truncate(stderr or ""), runtime_ms=runtime_ms, sandbox_image=image_id)
        if timed_out:
            base["stderr"] += f"\n[sandbox] killed after wall-clock timeout of {limits.timeout_s}s"
            return ExecutionResult(status=ExecutionStatus.TIMEOUT, **base)
        files, problem = self._scan_output(out)
        base["output_files"] = files
        if oom:
            base["stderr"] += f"\n[sandbox] killed: memory limit of {limits.memory_mb} MB exceeded (OOM)"
            return ExecutionResult(status=ExecutionStatus.RUNTIME_ERROR, **base)
        if proc.returncode == 125:
            return ExecutionResult(status=ExecutionStatus.SANDBOX_UNAVAILABLE, **base)
        if problem:
            base["stderr"] += f"\n[sandbox] {problem[1]}"
            return ExecutionResult(status=problem[0], **base)
        if proc.returncode != 0:
            return ExecutionResult(status=ExecutionStatus.RUNTIME_ERROR, **base)
        return ExecutionResult(status=ExecutionStatus.SUCCESS, **base)

    def _kill(self, name: str) -> None:
        try:
            self._docker("kill", name, timeout=30)
        except (OSError, subprocess.TimeoutExpired):
            pass

    def _remove(self, name: str) -> None:
        try:
            self._docker("rm", "-f", name, timeout=30)
        except (OSError, subprocess.TimeoutExpired):
            pass

    def _scan_output(self, out: Path) -> tuple[list[str], tuple[ExecutionStatus, str] | None]:
        """Regular files in output_dir. Symlinks / special files are removed and flagged."""
        files, total, problem = [], 0, None
        for p in sorted(out.rglob("*")):
            st = p.lstat()
            if stat.S_ISLNK(st.st_mode) or not (stat.S_ISREG(st.st_mode) or stat.S_ISDIR(st.st_mode)):
                p.unlink(missing_ok=True)
                problem = (ExecutionStatus.SECURITY_VIOLATION, f"removed non-regular output entry {p.name}")
                continue
            if stat.S_ISREG(st.st_mode):
                files.append(str(p))
                total += st.st_size
        if problem is None and total > self.max_output_bytes:
            problem = (ExecutionStatus.INVALID_OUTPUT, f"output size {total} bytes exceeds limit")
        return files, problem
