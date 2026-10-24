import pytest

from smk.app.timestep import FixedTimestep

TICK = 1 / 60


def test_partial_frames_accumulate_into_a_tick():
    timestep = FixedTimestep(TICK, max_frame_ticks=5)
    assert timestep.advance(TICK * 0.6) == 0
    assert timestep.alpha == pytest.approx(0.6)
    assert timestep.advance(TICK * 0.6) == 1
    assert timestep.alpha == pytest.approx(0.2)


def test_high_refresh_display_still_gets_60_ticks_a_second():
    timestep = FixedTimestep(TICK, max_frame_ticks=5)
    ticks = sum(timestep.advance(1 / 144) for _ in range(144))
    assert ticks == 60


def test_long_hitch_is_clamped():
    timestep = FixedTimestep(TICK, max_frame_ticks=5)
    assert timestep.advance(3.0) == 5


def test_negative_frame_time_is_ignored():
    timestep = FixedTimestep(TICK, max_frame_ticks=5)
    assert timestep.advance(-1.0) == 0
    assert timestep.alpha == 0.0
