"""Offline tests: concurrency helper, rate limiter, and thread/process-safe usage limits (B1)."""

from __future__ import annotations

import json
import multiprocessing as mp
import threading
import time

import pytest

from src.bedrock.client import BedrockClient, ModelInvocationError, RetryPolicy
from src.bedrock.concurrency import ModelRateLimiter, TaskResult, map_concurrent, run_concurrent
from src.bedrock.models import ConcurrencySettings, RateLimitSettings, load_registry
from src.bedrock.usage import BudgetExceeded, CostTracker, UsageLimits


# ------------------------------------------------------------------ run_concurrent
def test_results_preserve_input_order():
    def task(i):
        def f():
            time.sleep(0.01 * (5 - i))  # later tasks finish first
            return i * i
        return f
    res = run_concurrent([task(i) for i in range(5)], max_workers=5)
    assert [r.index for r in res] == list(range(5))
    assert [r.value for r in res] == [0, 1, 4, 9, 16]


def test_exceptions_are_returned_per_task_not_swallowed():
    def boom():
        raise RuntimeError("task 1 failed")
    res = run_concurrent([lambda: "a", boom, lambda: "c"], max_workers=3)
    assert [r.ok for r in res] == [True, False, True]
    assert isinstance(res[1].error, RuntimeError) and str(res[1].error) == "task 1 failed"
    with pytest.raises(RuntimeError, match="task 1 failed"):
        res[1].unwrap()
    assert res[2].unwrap() == "c"


def test_max_workers_bounds_parallelism():
    active, peak, lock = [0], [0], threading.Lock()

    def task():
        with lock:
            active[0] += 1
            peak[0] = max(peak[0], active[0])
        time.sleep(0.02)
        with lock:
            active[0] -= 1
    run_concurrent([task] * 12, max_workers=3)
    assert peak[0] <= 3


def test_map_concurrent_and_validation():
    res = map_concurrent(lambda x: x + 1, [1, 2, 3], max_workers=2)
    assert [r.value for r in res] == [2, 3, 4]
    assert run_concurrent([], max_workers=4) == []
    with pytest.raises(ValueError):
        run_concurrent([lambda: 1], max_workers=0)
    assert isinstance(res[0], TaskResult)


# ------------------------------------------------------------------ rate limiter
class FakeClock:
    def __init__(self):
        self.t = 0.0
        self.sleeps = []
        self.lock = threading.Lock()

    def now(self):
        return self.t

    def sleep(self, s):
        with self.lock:
            self.sleeps.append(s)


def test_rate_limiter_spaces_requests_per_model():
    clk = FakeClock()
    rl = ModelRateLimiter({"A": 2.0}, default_interval_s=0.0, clock=clk.now, sleep=clk.sleep)
    waits = [rl.acquire("A") for _ in range(3)]
    assert waits == [0.0, 2.0, 4.0]          # slots at t=0, 2, 4
    assert rl.acquire("B") == 0.0            # other models unaffected
    clk.t = 10.0
    assert rl.acquire("A") == 0.0            # slot already free


def test_rate_limiter_threaded_slots_are_unique():
    clk = FakeClock()
    rl = ModelRateLimiter({"A": 1.0}, clock=clk.now, sleep=clk.sleep)
    res = run_concurrent([lambda: rl.acquire("A")] * 10, max_workers=10)
    assert sorted(r.value for r in res) == [float(i) for i in range(10)]


def test_rate_limit_settings_from_config():
    s = RateLimitSettings(min_interval_s=0.5, requests_per_minute=30)
    assert s.interval_s == 2.0
    cs = ConcurrencySettings(max_workers=2, default=RateLimitSettings(requests_per_minute=60),
                             per_model={"C": RateLimitSettings(min_interval_s=5)})
    rl = ModelRateLimiter.from_settings(cs, ["A", "C"])
    assert rl.interval("A") == 1.0 and rl.interval("C") == 5.0 and rl.interval("Z") == 1.0


def test_models_yaml_concurrency_block_loads():
    reg = load_registry()
    assert reg.concurrency.max_workers >= 1
    assert set(reg.concurrency.per_model) <= set(reg.aliases)


def test_unknown_alias_in_concurrency_rejected(tmp_path):
    import yaml
    from src.bedrock.models import DEFAULT_MODELS_CONFIG
    raw = yaml.safe_load(DEFAULT_MODELS_CONFIG.read_text())
    raw["concurrency"] = {"per_model": {"Z": {"requests_per_minute": 1}}}
    p = tmp_path / "m.yaml"
    p.write_text(yaml.safe_dump(raw))
    with pytest.raises(ValueError, match="unknown aliases"):
        load_registry(p)


def test_client_paces_every_attempt(tmp_path):
    from tests.test_bedrock_client import FakeRuntime, client_error, ok_response
    clk = FakeClock()
    reg = load_registry()
    rl = ModelRateLimiter({"A": 3.0}, clock=clk.now, sleep=clk.sleep)
    c = BedrockClient(reg, runtime_client=FakeRuntime([client_error("ThrottlingException"), ok_response()]),
                      log_path=tmp_path / "i.jsonl", ledger_path=tmp_path / "l.json", cache_dir=None,
                      retry=RetryPolicy(max_attempts=3, base_delay_s=0.0), sleep=lambda s: None, rate_limiter=rl)
    res = c.converse("A", "hi")
    assert clk.sleeps == [3.0]                  # retry waited for its pacing slot
    assert res.record.rate_limit_wait_ms == pytest.approx(3000.0)


# ------------------------------------------------------- B1: no overshoot under threads
class AlwaysOK:
    def __init__(self):
        self.n = 0
        self.lock = threading.Lock()

    def converse(self, **kw):
        time.sleep(0.005)  # widen the race window
        with self.lock:
            self.n += 1
        return {"output": {"message": {"content": [{"text": "OK"}]}},
                "usage": {"inputTokens": 10, "outputTokens": 5}, "stopReason": "end_turn"}


def test_B1_threads_cannot_overshoot_call_limit(tmp_path):
    rt = AlwaysOK()
    c = BedrockClient(load_registry(), runtime_client=rt, log_path=tmp_path / "i.jsonl",
                      ledger_path=tmp_path / "l.json", cache_dir=None, sleep=lambda s: None,
                      rate_limiter=ModelRateLimiter(), limits=UsageLimits(max_calls=5))
    res = run_concurrent([lambda i=i: c.converse("A", f"p{i}", max_tokens=10) for i in range(30)], max_workers=16)
    assert rt.n == 5 and c.costs.calls == 5
    assert sum(r.ok for r in res) == 5
    refused = [r.error for r in res if not r.ok]
    assert all(isinstance(e, ModelInvocationError) and e.record.status == "budget_refused" for e in refused)
    assert c.costs.reserved_calls == 0


def test_B1_threads_cannot_overshoot_output_token_limit(tmp_path):
    rt = AlwaysOK()
    c = BedrockClient(load_registry(), runtime_client=rt, log_path=tmp_path / "i.jsonl",
                      ledger_path=tmp_path / "l.json", cache_dir=None, sleep=lambda s: None,
                      rate_limiter=ModelRateLimiter(), limits=UsageLimits(max_output_tokens=1000))
    run_concurrent([lambda i=i: c.converse("A", f"p{i}", max_tokens=300) for i in range(20)], max_workers=20)
    assert rt.n == 3  # 3 * 300 worst case <= 1000 < 4 * 300, regardless of interleaving


def test_B1_identical_concurrent_requests_make_one_paid_call(tmp_path):
    rt = AlwaysOK()
    c = BedrockClient(load_registry(), runtime_client=rt, log_path=tmp_path / "i.jsonl",
                      ledger_path=tmp_path / "l.json", cache_dir=tmp_path / "cache", sleep=lambda s: None,
                      rate_limiter=ModelRateLimiter())
    res = run_concurrent([lambda: c.converse("A", "same", max_tokens=10)] * 8, max_workers=8)
    assert rt.n == 1 and sum(r.value.record.from_cache for r in res) == 7


# ----------------------------------------------- B1: shared ledger across clients/processes
def test_B1_two_trackers_share_one_ledger(tmp_path):
    led = tmp_path / "l.json"
    t1, t2 = CostTracker(led, UsageLimits(max_calls=2)), CostTracker(led, UsageLimits(max_calls=2))
    r1 = t1.reserve(est_input_tokens=1, max_output_tokens=1, worst_case_usd=None)
    r2 = t2.reserve(est_input_tokens=1, max_output_tokens=1, worst_case_usd=None)
    with pytest.raises(BudgetExceeded):
        t1.reserve(est_input_tokens=1, max_output_tokens=1, worst_case_usd=None)
    r1.attempts_made = r2.attempts_made = 1
    t1.settle(r1, input_tokens=5, output_tokens=5, cost_usd=None)
    t2.settle(r2, input_tokens=7, output_tokens=7, cost_usd=None)  # no last-writer-wins loss
    d = json.loads(led.read_text())
    assert d["calls"] == 2 and d["input_tokens"] == 12 and d["pending"] == {}


def test_B1_stale_reservation_of_dead_process_is_dropped(tmp_path):
    led = tmp_path / "l.json"
    led.write_text(json.dumps({"calls": 0, "pending": {
        "dead": {"calls": 1, "input_tokens": 1, "output_tokens": 1, "usd": 0, "pid": 2 ** 22 + 12345}}}))
    t = CostTracker(led, UsageLimits(max_calls=1))
    t.reserve(est_input_tokens=1, max_output_tokens=1, worst_case_usd=None)  # would fail if stale entry counted


def _proc_worker(ledger: str, n: int, q) -> None:
    t = CostTracker(ledger, UsageLimits(max_calls=10, max_input_tokens=10**9, max_output_tokens=10**9))
    ok = 0
    for _ in range(n):
        try:
            r = t.reserve(est_input_tokens=1, max_output_tokens=1, worst_case_usd=None)
        except BudgetExceeded:
            continue
        r.attempts_made = 1
        time.sleep(0.002)
        t.settle(r, input_tokens=1, output_tokens=1, cost_usd=None)
        ok += 1
    q.put(ok)


def test_B1_processes_cannot_overshoot_shared_ledger(tmp_path):
    ctx = mp.get_context("spawn")
    q = ctx.Queue()
    led = str(tmp_path / "l.json")
    procs = [ctx.Process(target=_proc_worker, args=(led, 8, q)) for _ in range(4)]
    for p in procs:
        p.start()
    for p in procs:
        p.join(60)
    total = sum(q.get(timeout=5) for _ in procs)
    d = json.loads(open(led).read())
    assert total == 10 and d["calls"] == 10 and d["pending"] == {}
