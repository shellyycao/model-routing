"""Run many independent invocations concurrently, with per-model pacing.

- `run_concurrent` executes callables on a bounded thread pool. Results come back in
  input order; a task's exception is captured in its TaskResult, never swallowed or
  raised past the other tasks.
- `ModelRateLimiter` spaces request starts per model by a minimum interval derived from
  configs/models.yaml (`concurrency:`). BedrockClient calls `acquire(alias)` before every
  API attempt, so pacing holds across threads and retries.

Hard call/token limits are enforced by CostTracker's reserve/settle, not here.
"""

from __future__ import annotations

import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, Callable, Generic, Iterable, Sequence, TypeVar

from .models import ConcurrencySettings, RateLimitSettings

R = TypeVar("R")
X = TypeVar("X")


@dataclass
class TaskResult(Generic[R]):
    index: int
    value: R | None = None
    error: BaseException | None = None

    @property
    def ok(self) -> bool:
        return self.error is None

    def unwrap(self) -> R:
        if self.error is not None:
            raise self.error
        return self.value  # type: ignore[return-value]


def run_concurrent(tasks: Sequence[Callable[[], R]], *, max_workers: int = 1) -> list[TaskResult[R]]:
    """Run zero-argument callables with at most `max_workers` threads.

    Returns one TaskResult per task, in input order. Exceptions (subclasses of
    Exception) are captured per task; KeyboardInterrupt/SystemExit still propagate.
    """
    if max_workers < 1:
        raise ValueError("max_workers must be >= 1")
    tasks = list(tasks)

    def _run(i: int) -> TaskResult[R]:
        try:
            return TaskResult(index=i, value=tasks[i]())
        except Exception as e:  # noqa: BLE001 - returned to caller, not swallowed
            return TaskResult(index=i, error=e)

    if max_workers == 1 or len(tasks) <= 1:
        return [_run(i) for i in range(len(tasks))]
    with ThreadPoolExecutor(max_workers=min(max_workers, len(tasks))) as pool:
        return list(pool.map(_run, range(len(tasks))))


def map_concurrent(fn: Callable[[X], R], items: Iterable[X], *, max_workers: int = 1) -> list[TaskResult[R]]:
    """`run_concurrent` over `fn(item)` for each item, preserving order."""
    return run_concurrent([lambda it=it: fn(it) for it in items], max_workers=max_workers)


class ModelRateLimiter:
    """Per-model minimum spacing between request starts, safe across threads.

    A caller reserves the next free slot under a lock, then sleeps outside the lock
    until that slot, so waiting threads do not block other models.
    """

    def __init__(
        self,
        intervals: dict[str, float] | None = None,
        *,
        default_interval_s: float = 0.0,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], Any] = time.sleep,
    ):
        self._intervals = dict(intervals or {})
        self._default = default_interval_s
        self._clock = clock
        self._sleep = sleep
        self._lock = threading.Lock()
        self._next: dict[str, float] = {}

    @classmethod
    def from_settings(cls, settings: ConcurrencySettings, aliases: Iterable[str] = (), **kw) -> "ModelRateLimiter":
        intervals = {a: settings.for_model(a).interval_s for a in aliases}
        intervals.update({a: s.interval_s for a, s in settings.per_model.items()})
        return cls(intervals, default_interval_s=settings.default.interval_s, **kw)

    def interval(self, model: str) -> float:
        return self._intervals.get(model, self._default)

    def acquire(self, model: str) -> float:
        """Block until `model` may start a request. Returns seconds waited."""
        interval = self.interval(model)
        if interval <= 0:
            return 0.0
        with self._lock:
            now = self._clock()
            slot = max(now, self._next.get(model, now))
            self._next[model] = slot + interval
        wait = slot - now
        if wait > 0:
            self._sleep(wait)
        return wait


__all__ = ["TaskResult", "run_concurrent", "map_concurrent", "ModelRateLimiter", "RateLimitSettings"]
