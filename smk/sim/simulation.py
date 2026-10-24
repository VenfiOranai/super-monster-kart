"""The simulation object and its snapshots (GDD §14.2)."""

import hashlib
from dataclasses import dataclass
from typing import NewType

from smk.sim.input import InputFrame
from smk.sim.rng import Rng

RacerId = NewType("RacerId", int)
"""A racer's stable ID. Racers are always processed in ID order, never dict order."""


@dataclass(frozen=True)
class WorldState:
    """An immutable copy of everything the simulation knows at one tick."""

    tick: int
    rng_state: int

    def state_hash(self) -> str:
        """A digest of the whole state, for determinism checks and desync detection.

        Built from ``repr``, which is exact and stable for the ints, floats and
        tuples a snapshot is made of.
        """
        return hashlib.sha256(repr(self).encode()).hexdigest()


class Simulation:
    """The pure, deterministic game world, advanced one fixed tick at a time.

    Same seed and same inputs always give the same state hash. Each tick runs
    in a fixed order (GDD §14.8): inputs → physics → collisions → attacks →
    damage → items → KO/standings. Racers and their phases arrive in later
    M1 slices; for now a tick only advances the clock.
    """

    def __init__(self, seed: int) -> None:
        self._tick = 0
        self._rng = Rng(seed)

    @property
    def tick(self) -> int:
        return self._tick

    def step(self, inputs: dict[RacerId, InputFrame]) -> None:
        """Advance exactly one tick (``consts.TICK_DURATION`` of game time)."""
        self._tick += 1

    def snapshot(self) -> WorldState:
        return WorldState(tick=self._tick, rng_state=self._rng.state)
