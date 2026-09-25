"""The fixed 320x180 render target and its integer-scaled presentation (GDD §12.1)."""

from dataclasses import dataclass

import pygame
from pygame._sdl2.video import Renderer, Texture

from smk import reporting


@dataclass(frozen=True)
class Viewport:
    """Where the internal buffer lands inside a window of a given size."""

    scale: int
    offset: tuple[int, int]
    size: tuple[int, int]

    @classmethod
    def fit(cls, buffer_size: tuple[int, int], window_size: tuple[int, int]) -> "Viewport":
        """Largest integer scale that fits, centred; the remainder is bars."""
        buffer_w, buffer_h = buffer_size
        window_w, window_h = window_size
        scale = max(1, min(window_w // buffer_w, window_h // buffer_h))
        size = (buffer_w * scale, buffer_h * scale)
        offset = ((window_w - size[0]) // 2, (window_h - size[1]) // 2)
        return cls(scale, offset, size)

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(self.offset, self.size)


class Screen:
    """A window that renders each frame into a fixed-size internal buffer.

    The buffer never changes size with the window — a bigger window gets
    bigger pixels, never more field of view.

    The integer scale happens on the GPU: the CPU uploads only the 320x180
    buffer each frame. Scaling on the CPU means writing every output pixel
    (8.3M at 4K), which blew the frame budget from 1440p up in the M0 spike.
    """

    INTERNAL_SIZE = (320, 180)
    DEFAULT_DESKTOP_FRACTION = 0.75
    BAR_COLOUR = (0, 0, 0)

    @classmethod
    def default_window_size(cls, desktop_size: tuple[int, int]) -> tuple[int, int]:
        """The largest exact integer scale that leaves room around the window on this desktop."""
        room = tuple(int(side * cls.DEFAULT_DESKTOP_FRACTION) for side in desktop_size)
        return Viewport.fit(cls.INTERNAL_SIZE, room).size

    def __init__(self, title: str, vsync: bool = True) -> None:
        """Needs pygame initialised; see ``smk.app.bootstrap.setup``."""
        desktop = pygame.display.get_desktop_sizes()[0]
        self._window = pygame.Window(title, size=self.default_window_size(desktop), resizable=True)
        self._window.minimum_size = self.INTERNAL_SIZE
        # 32-bit so renderers can write packed pixels through surfarray.pixels2d.
        self._buffer = pygame.Surface(self.INTERNAL_SIZE, depth=32)
        self._renderer = Renderer(self._window, vsync=vsync)
        self._renderer.draw_color = self.BAR_COLOUR
        # scale_quality 0 is nearest-neighbour sampling — never filter the pixel grid.
        self._texture = Texture(self._renderer, self.INTERNAL_SIZE, streaming=True, scale_quality=0)

    @property
    def buffer(self) -> pygame.Surface:
        return self._buffer

    @property
    def window(self) -> pygame.Window:
        return self._window

    def render(self) -> None:
        """Integer-scale the buffer into the window and flip."""
        with reporting.reporter.measure("upload"):
            self._texture.update(self._buffer)
        with reporting.reporter.measure("scale"):
            # Clearing every frame paints the bars; the back buffer is undefined after a present.
            self._renderer.clear()
            viewport = Viewport.fit(self.INTERNAL_SIZE, self._renderer.get_viewport().size)
            self._texture.draw(dstrect=viewport.rect)
        with reporting.reporter.measure("flip"):
            self._renderer.present()
