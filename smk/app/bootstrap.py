"""Process-level setup that has to happen before anything touches pygame."""

import os

import pygame


def setup() -> None:
    """Configure the platform and initialise pygame. Call once, before creating the game.

    The caller owns the pygame lifetime from here and must ``pygame.quit()``.
    """
    # Without per-monitor DPI awareness, Windows hands a scaled display to the
    # game at a fraction of its real resolution and then stretches the window
    # back up with a smoothing filter, which blurs the pixel grid and makes
    # every integer-scale decision against the wrong size. SDL reads this hint
    # when video initialises, so it must be set before pygame.init().
    os.environ.setdefault("SDL_WINDOWS_DPI_AWARENESS", "permonitorv2")
    pygame.init()
