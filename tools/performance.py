"""A reporter that records how long each frame stage takes."""

import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass

import numpy as np

from smk.reporting import Reporter


@dataclass(frozen=True)
class StageStats:
    mean_ms: float
    p99_ms: float
    max_ms: float

    @classmethod
    def of(cls, samples_ms: list[float]) -> "StageStats":
        values = np.asarray(samples_ms)
        return cls(float(values.mean()), float(np.percentile(values, 99)), float(values.max()))


class PerformanceReporter(Reporter):
    """Collects the duration of each measured stage, per frame, until reset.

    Uses a monotonic clock. ``frame`` is recorded by ``end_frame`` and covers
    everything between frames, not just the measured stages.
    """

    def __init__(self, clock: Callable[[], float] = time.perf_counter) -> None:
        self._clock = clock
        self._samples: dict[str, list[float]] = {}
        self._frame_start = clock()

    @contextmanager
    def measure(self, name: str) -> Iterator[None]:
        start = self._clock()
        try:
            yield
        finally:
            self._record(name, self._clock() - start)

    def end_frame(self) -> None:
        now = self._clock()
        self._record("frame", now - self._frame_start)
        self._frame_start = now

    @property
    def frame_count(self) -> int:
        return len(self._samples.get("frame", ()))

    def samples(self, name: str) -> list[float]:
        """Every recorded duration for one stage, in milliseconds, oldest first."""
        return list(self._samples.get(name, ()))

    def stats(self) -> dict[str, StageStats]:
        return {name: StageStats.of(samples) for name, samples in self._samples.items()}

    def total(self, excluding: tuple[str, ...] = ()) -> StageStats:
        """Per-frame sum of the measured stages (not ``frame``), minus any excluded."""
        stages = [name for name in self._samples if name != "frame" and name not in excluding]
        return StageStats.of([sum(parts) for parts in zip(*(self._samples[name] for name in stages))])

    def reset(self) -> None:
        self._samples.clear()
        self._frame_start = self._clock()

    def _record(self, name: str, seconds: float) -> None:
        self._samples.setdefault(name, []).append(seconds * 1000)
