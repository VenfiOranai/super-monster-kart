import pytest

from tools.performance import PerformanceReporter


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def test_stages_and_frames_are_recorded_in_milliseconds():
    clock = FakeClock()
    performance = PerformanceReporter(clock)
    for stage_seconds in (0.001, 0.003):
        with performance.measure("draw"):
            clock.now += stage_seconds
        clock.now += 0.001
        performance.end_frame()

    stats = performance.stats()
    assert performance.samples("draw") == pytest.approx([1.0, 3.0])
    assert stats["draw"].mean_ms == pytest.approx(2.0)
    assert stats["draw"].max_ms == pytest.approx(3.0)
    assert stats["frame"].mean_ms == pytest.approx(3.0)
    assert performance.frame_count == 2


def test_reset_discards_samples_and_restarts_the_frame_clock():
    clock = FakeClock()
    performance = PerformanceReporter(clock)
    clock.now = 5.0
    performance.end_frame()
    performance.reset()
    clock.now = 5.002
    performance.end_frame()
    assert performance.samples("frame") == pytest.approx([2.0])


def test_total_sums_measured_stages_per_frame():
    clock = FakeClock()
    performance = PerformanceReporter(clock)
    for draw, flip in ((0.001, 0.002), (0.003, 0.004)):
        with performance.measure("draw"):
            clock.now += draw
        with performance.measure("flip"):
            clock.now += flip
        performance.end_frame()

    assert performance.total().mean_ms == pytest.approx(5.0)
    assert performance.total(excluding=("flip",)).max_ms == pytest.approx(3.0)
