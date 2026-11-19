"""DockerExecutor tests.

Part 1 (always run): the docker argv carries every isolation flag; the CLI env is scrubbed; an
unavailable daemon yields SANDBOX_UNAVAILABLE and never runs the code on the host.
Part 2 (need a running daemon + built image; otherwise SKIPPED with the reason): one test per
isolation control, each demonstrated by actually running code in the sandbox.
"""

import json
import os
import subprocess
import textwrap
from pathlib import Path

import pytest

from datasets.generate import PROJECTS_DIR
from src.contracts import ExecutionStatus, ResourceLimits
from src.evaluation.analysis import validate_analysis
from src.evaluation.cleaning import validate_cleaning
from src.workflow.executor import DEFAULT_IMAGE, IMAGE_LEASE_LABEL, DockerExecutor, docker_cli_env

SOLUTIONS = Path(__file__).parent / "fixtures" / "benchmark" / "solutions"


# --------------------------------------------------------------------------- part 1: no daemon needed

def _cmd(tmp_path, **lim):
    code = tmp_path / "main.py"
    code.write_text("print(1)")
    inp = tmp_path / "raw.csv"
    inp.write_text("a\n1\n")
    out = tmp_path / "out"
    out.mkdir()
    return DockerExecutor().build_run_command("c1", code, {"raw.csv": str(inp)}, out, ResourceLimits(**lim)), tmp_path


def test_run_command_has_every_isolation_flag(tmp_path):
    cmd, base = _cmd(tmp_path, memory_mb=256, cpus=0.5)
    s = " ".join(cmd)
    for flag in ["--network none", "--read-only", "--memory 256m", "--memory-swap 256m", "--cpus 0.5",
                 "--pids-limit 128", "--user 10001:10001", "--cap-drop ALL",
                 "--security-opt no-new-privileges", "--ipc none"]:
        assert flag in s, flag
    assert any(p.startswith("/tmp:") and "noexec" in p for p in cmd)
    mounts = [cmd[i + 1] for i, p in enumerate(cmd) if p == "--mount"]
    assert len(mounts) == 3
    assert all(m.endswith(",readonly") for m in mounts if "/sandbox/output" not in m)
    rw = [m for m in mounts if not m.endswith(",readonly")]
    assert len(rw) == 1 and rw[0].endswith("target=/sandbox/output")
    assert not any(m for m in mounts if str(Path.home() / ".aws") in m or f"source={Path.home()}," in m)
    envs = [cmd[i + 1] for i, p in enumerate(cmd) if p in ("--env", "-e")]
    assert envs == ["INPUT_DIR=/sandbox/input", "OUTPUT_DIR=/sandbox/output"]
    assert "--env-file" not in cmd and "--privileged" not in cmd


def test_image_lease_command_isolated_and_never_pulls():
    cmd = DockerExecutor().build_image_lease_command("lease-1")
    s = " ".join(cmd)
    for flag in ["--detach", "--pull never", f"--label {IMAGE_LEASE_LABEL}", "--network none",
                 "--read-only", "--memory 32m", "--memory-swap 32m", "--cpus 0.1",
                 "--pids-limit 16", "--user 10001:10001", "--cap-drop ALL",
                 "--security-opt no-new-privileges", "--ipc none", "--restart no"]:
        assert flag in s, flag
    assert "--entrypoint /bin/sleep" in s and cmd[-2:] == [DEFAULT_IMAGE, "infinity"]
    assert "--mount" not in cmd and "--env" not in cmd and "--env-file" not in cmd


def test_image_lease_checks_id_and_cleans_up(monkeypatch):
    ex = DockerExecutor()
    calls = []
    monkeypatch.setattr(ex, "availability", lambda: (True, "sha256:verified"))

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, stdout="holder\n", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    removed = []
    monkeypatch.setattr(ex, "_remove", removed.append)
    with ex.image_lease("sha256:verified") as name:
        assert name.startswith("mrx-sbx-lease-")
    assert calls and calls[0][1:4] == ["run", "--detach", "--pull"]
    assert removed == [name]


def test_image_lease_refuses_wrong_verified_id(monkeypatch):
    ex = DockerExecutor()
    monkeypatch.setattr(ex, "availability", lambda: (True, "sha256:other"))
    with pytest.raises(RuntimeError, match="local image ID"):
        with ex.image_lease("sha256:verified"):
            pass


def test_network_limit_true_is_refused(tmp_path):
    with pytest.raises(ValueError):
        _cmd(tmp_path, network=True)


def test_bad_input_names_and_paths_rejected(tmp_path):
    ex = DockerExecutor()
    code = tmp_path / "main.py"
    code.write_text("")
    for bad in ["../x", "a/b", ".hidden", ""]:
        with pytest.raises(ValueError):
            ex.build_run_command("c", code, {bad: str(code)}, tmp_path, ResourceLimits())
    weird = tmp_path / "a,readonly=false"
    weird.write_text("")
    with pytest.raises(ValueError):
        ex.build_run_command("c", code, {"x.csv": str(weird)}, tmp_path, ResourceLimits())


def test_cli_env_drops_credentials(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "SENTINEL_NOT_A_REAL_KEY")
    monkeypatch.setenv("AWS_PROFILE", "x")
    monkeypatch.setenv("SOME_TOKEN", "y")
    env = docker_cli_env()
    assert not any(k.startswith("AWS") for k in env) and "SOME_TOKEN" not in env
    assert "SENTINEL_NOT_A_REAL_KEY" not in json.dumps(env)


def test_unavailable_docker_returns_sandbox_unavailable_and_never_runs_on_host(tmp_path):
    marker = tmp_path / "ran_on_host"
    code = f"open({str(marker)!r}, 'w').write('x')"
    for ex in [DockerExecutor(docker_bin=str(tmp_path / "no-such-docker")),
               DockerExecutor(docker_bin="false")]:          # CLI present but daemon check fails
        res = ex.execute(code, {}, str(tmp_path / "out"))
        assert res.status == ExecutionStatus.SANDBOX_UNAVAILABLE
        assert not marker.exists()


# --------------------------------------------------------------------------- part 2: real sandbox

_EX = DockerExecutor()
_AVAILABLE, _REASON = _EX.availability()
needs_sandbox = pytest.mark.skipif(not _AVAILABLE, reason=f"UNVERIFIED - sandbox not available: {_REASON}")


@needs_sandbox
def test_real_image_lease_holds_verified_image():
    ok, image_id = _EX.availability()
    assert ok
    with _EX.image_lease(image_id) as name:
        state = _EX._docker("inspect", "--format", "{{.State.Running}}", name)
        assert state.returncode == 0 and state.stdout.strip() == "true"
        assert _EX.availability() == (True, image_id)
    gone = _EX._docker("inspect", name)
    assert gone.returncode != 0


def _run(tmp_path, code, inputs=None, **lim):
    out = tmp_path / "out"
    res = _EX.execute(textwrap.dedent(code), inputs or {}, str(out), ResourceLimits(**{"timeout_s": 60, **lim}))
    return res, out


@needs_sandbox
def test_isolation_no_network(tmp_path):
    res, _ = _run(tmp_path, """
        import socket
        results = []
        for host, port in [("1.1.1.1", 53), ("8.8.8.8", 443)]:
            try:
                socket.create_connection((host, port), timeout=3); results.append("CONNECTED")
            except OSError: results.append("blocked")
        try:
            socket.getaddrinfo("example.com", 443); results.append("DNS_OK")
        except OSError: results.append("dns_blocked")
        import os, json, subprocess
        up = []
        for n in sorted(os.listdir("/sys/class/net")):
            p = f"/sys/class/net/{n}"
            if os.path.isdir(p) and int(open(p + "/flags").read(), 16) & 1:   # IFF_UP
                up.append(n)
        v4_routes = open("/proc/net/route").read().splitlines()[1:]
        v6_routes = [l for l in open("/proc/net/ipv6_route") if l.split()[-1] != "lo"]
        # Without CAP_NET_ADMIN the code must not be able to bring an interface up.
        import fcntl, struct
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            ifr = struct.pack("16sH14s", b"tunl0", 0x1, b"\\x00" * 14)
            fcntl.ioctl(s.fileno(), 0x8914, ifr)   # SIOCSIFFLAGS
            raise_up = "RAISED"
        except OSError:
            raise_up = "denied"
        print(json.dumps({"results": results, "up": up, "v4_routes": v4_routes,
                          "v6_routes": v6_routes, "raise_up": raise_up}))
    """)
    assert res.status == ExecutionStatus.SUCCESS, res.stderr
    import json
    out = json.loads(res.stdout.strip().splitlines()[-1])
    assert "CONNECTED" not in out["results"] and "DNS_OK" not in out["results"]
    # Lead correction 2026-11-18 (documented in docs/reviews/2026-11-18_sandbox_verification.md):
    # Docker Desktop's LinuxKit kernel creates DOWN fallback tunnel devices (tunl0, gre0, ...) in every
    # network namespace, so "the only interface is lo" is not the control. The control is: only the
    # loopback interface is up, there are no routes, and the code cannot raise an interface.
    assert out["up"] == ["lo"], out["up"]
    assert out["v4_routes"] == [] and out["v6_routes"] == [], out
    assert out["raise_up"] == "denied"


@needs_sandbox
def test_isolation_no_aws_env_or_credentials(tmp_path, monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "SENTINEL_NOT_A_REAL_KEY")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "SENTINEL_NOT_A_REAL_SECRET")
    res, _ = _run(tmp_path, f"""
        import os, json
        print(json.dumps({{
            "env": sorted(os.environ),
            "aws_dirs": [p for p in ["/root/.aws", "/tmp/.aws", os.path.expanduser("~/.aws"),
                                     {str(Path.home() / '.aws')!r}] if os.path.exists(p)],
            "home_visible": os.path.exists({str(Path.home())!r}),
        }}))
    """)
    assert res.status == ExecutionStatus.SUCCESS, res.stderr
    info = json.loads(res.stdout)
    assert not [k for k in info["env"] if k.startswith("AWS")]
    assert info["aws_dirs"] == [] and info["home_visible"] is False
    assert "SENTINEL" not in res.stdout + res.stderr
    assert set(info["env"]) <= {"PATH", "HOME", "LANG", "GPG_KEY", "PYTHON_VERSION", "PYTHON_SHA256",
                                "PYTHONDONTWRITEBYTECODE", "PYTHONUNBUFFERED", "PIP_NO_CACHE_DIR",
                                "PIP_DISABLE_PIP_VERSION_CHECK", "MPLCONFIGDIR", "INPUT_DIR", "OUTPUT_DIR",
                                "HOSTNAME", "LC_CTYPE"}, info["env"]


@needs_sandbox
def test_isolation_cannot_write_outside_output_dir(tmp_path):
    res, out = _run(tmp_path, """
        import os
        ok = []
        for p in ["/etc/x", "/x", "/sandbox/code/x", "/sandbox/input/x", "/usr/local/lib/x", "/home/x"]:
            try:
                open(p, "w").write("x"); ok.append(p)
            except OSError: pass
        open("/sandbox/output/result.txt", "w").write("ok")
        print("WROTE", ok)
    """)
    assert res.status == ExecutionStatus.SUCCESS, res.stderr
    assert "WROTE []" in res.stdout
    assert [Path(f).name for f in res.output_files] == ["result.txt"]


@needs_sandbox
def test_isolation_inputs_read_only(tmp_path):
    inp = tmp_path / "raw.csv"
    inp.write_text("a\n1\n")
    res, _ = _run(tmp_path, """
        import os
        try:
            open("/sandbox/input/raw.csv", "a").write("tamper"); print("TAMPERED")
        except OSError as e: print("readonly", e.errno)
        try:
            os.remove("/sandbox/input/raw.csv"); print("DELETED")
        except OSError: print("nodelete")
    """, {"raw.csv": str(inp)})
    assert res.status == ExecutionStatus.SUCCESS, res.stderr
    assert "TAMPERED" not in res.stdout and "DELETED" not in res.stdout
    assert inp.read_text() == "a\n1\n"


@needs_sandbox
def test_isolation_non_root_and_no_privilege_escalation(tmp_path):
    res, _ = _run(tmp_path, """
        import os
        print("uid", os.getuid(), os.geteuid(), os.getgid())
        try:
            os.setuid(0); print("BECAME_ROOT")
        except PermissionError: print("setuid_denied")
        print(open("/proc/self/status").read().split("CapEff:")[1].split()[0])
    """)
    assert res.status == ExecutionStatus.SUCCESS, res.stderr
    assert "uid 10001 10001 10001" in res.stdout and "BECAME_ROOT" not in res.stdout
    assert "0000000000000000" in res.stdout          # no effective capabilities


@needs_sandbox
def test_isolation_memory_limit(tmp_path):
    res, _ = _run(tmp_path, """
        blocks = []
        for _ in range(64):
            blocks.append(b"\x01" * (16 * 1024 * 1024))   # pages really touched; up to 1 GiB
        print("ALLOCATED", len(blocks))
    """, memory_mb=128)
    assert res.status == ExecutionStatus.RUNTIME_ERROR, (res.status, res.stdout, res.stderr)
    assert "ALLOCATED" not in res.stdout


@needs_sandbox
def test_isolation_timeout_kills_container(tmp_path):
    res, _ = _run(tmp_path, "while True:\n    pass\n", timeout_s=3)
    assert res.status == ExecutionStatus.TIMEOUT
    assert res.runtime_ms < 30_000
    left = subprocess.run(["docker", "ps", "-aq", "--filter", "name=mrx-sbx-"], capture_output=True, text=True,
                          env=docker_cli_env())
    assert left.stdout.strip() == ""


@needs_sandbox
def test_runtime_error_status(tmp_path):
    res, _ = _run(tmp_path, "raise SystemExit(3)")
    assert res.status == ExecutionStatus.RUNTIME_ERROR and res.exit_code == 3


@needs_sandbox
@pytest.mark.parametrize("pid", ["retail_sales", "customer_churn", "energy_consumption"])
def test_end_to_end_reference_solutions_in_sandbox(tmp_path, pid):
    """The independent pandas solutions run inside the sandbox and pass the validators."""
    pdir = PROJECTS_DIR / pid
    clean_res, out1 = _run(tmp_path / "c", (SOLUTIONS / f"{pid}_clean.py").read_text(),
                           {"raw.csv": str(pdir / "raw.csv")})
    assert clean_res.status == ExecutionStatus.SUCCESS, clean_res.stderr
    assert validate_cleaning(out1 / "cleaned.csv", pdir).hard_pass
    an_res, out2 = _run(tmp_path / "a", (SOLUTIONS / f"{pid}_analysis.py").read_text(),
                        {"cleaned.csv": str(out1 / "cleaned.csv")})
    assert an_res.status == ExecutionStatus.SUCCESS, an_res.stderr
    assert validate_analysis(out2 / "findings.json", pdir).hard_pass
    assert an_res.sandbox_image and an_res.sandbox_image.startswith("sha256:")
