"""Fixed-timestep accounting for the main loop (GDD §14.3)."""


class FixedTimestep:
    """Turns variable frame times into a whole number of fixed ticks.

    Each frame, ``advance`` reports how many ticks to simulate, and ``alpha``
    how far the leftover time reaches toward the next tick — the blend factor
    for drawing between the previous and current snapshots.
    """

    _TOLERANCE = 1e-6
    """In ticks: about 17 ns at 60 Hz."""

    def __init__(self, tick_duration: float, max_frame_ticks: int) -> None:
        self._tick_duration = tick_duration
        self._max_frame_dt = tick_duration * max_frame_ticks
        self._accumulator = 0.0

    @property
    def alpha(self) -> float:
        """Fraction of a tick left over, in [0, 1)."""
        return self._accumulator / self._tick_duration

    def advance(self, frame_dt: float) -> int:
        """Bank ``frame_dt`` seconds and return how many ticks are now due.

        A long hitch is clamped, dropping game time rather than queueing a
        backlog that takes longer to simulate than it took to accrue.
        """
        self._accumulator += min(max(frame_dt, 0.0), self._max_frame_dt)
        # The tolerance stops rounding error from leaving a tick a hair short:
        # (5 * TICK) // TICK is 4.0 in floating point.
        ticks = int(self._accumulator / self._tick_duration + self._TOLERANCE)
        self._accumulator = max(self._accumulator - ticks * self._tick_duration, 0.0)
        return ticks
