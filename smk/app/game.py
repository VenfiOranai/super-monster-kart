import pygame

from smk.render.screen import Screen


class Game:
    """Owns the pygame lifetime and the main loop.

    For now the loop only pumps events and renders a blank frame. The fixed
    60 Hz sim tick with interpolated rendering (GDD §14.3) slots in here once
    there is a simulation to step.
    """

    TITLE = "Super Monster Kart"

    def __init__(self) -> None:
        pygame.init()
        self._screen = Screen(self.TITLE)
        self._running = False

    def run(self) -> None:
        self._running = True
        try:
            while self._running:
                self._handle_events()
                self._screen.render()
        finally:
            pygame.quit()

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self._running = False
