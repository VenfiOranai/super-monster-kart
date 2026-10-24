import secrets
import time

import pygame

from smk import consts
from smk.app.timestep import FixedTimestep
from smk.render.screen import Screen
from smk.sim.simulation import Simulation


class Game:
    """Owns the main loop, and shuts pygame down when it ends.

    The simulation steps at a fixed 60 Hz while rendering runs as fast as the
    display allows (GDD §14.3). There is nothing to draw yet, so each frame is
    blank; once racers exist, frames blend the last two snapshots by
    ``FixedTimestep.alpha``.
    """

    TITLE = "Super Monster Kart"

    def __init__(self) -> None:
        self._screen = Screen(self.TITLE)
        self._simulation = Simulation(seed=secrets.randbits(64))
        self._timestep = FixedTimestep(consts.TICK_DURATION, consts.MAX_FRAME_TICKS)
        self._running = False

    def run(self) -> None:
        self._running = True
        # perf_counter is monotonic: a system clock change can't inject or swallow ticks.
        last = time.perf_counter()
        try:
            while self._running:
                now = time.perf_counter()
                frame_dt, last = now - last, now
                self._handle_events()
                for _ in range(self._timestep.advance(frame_dt)):
                    self._simulation.step({})
                self._screen.render()
        finally:
            pygame.quit()

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self._running = False
