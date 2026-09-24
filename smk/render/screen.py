"""The fixed 320x180 render target and its integer-scaled presentation (GDD §12.1)."""

from dataclasses import dataclass

import pygame


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


class Screen:
    """A window that renders each frame into a fixed-size internal buffer.

    The buffer never changes size with the window — a bigger window gets
    bigger pixels, never more field of view.
    """

    INTERNAL_SIZE = (320, 180)
    DEFAULT_SCALE = 4
    BAR_COLOUR = (0, 0, 0)
    CLEAR_COLOUR = (24, 24, 32)

    def __init__(self, title: str) -> None:
        width, height = self.INTERNAL_SIZE
        self._window = pygame.Window(
            title,
            size=(width * self.DEFAULT_SCALE, height * self.DEFAULT_SCALE),
            resizable=True,
        )
        self._window.minimum_size = self.INTERNAL_SIZE
        self._buffer = pygame.Surface(self.INTERNAL_SIZE)

    def render(self) -> None:
        self._buffer.fill(self.CLEAR_COLOUR)
        self._present()

    def _present(self) -> None:
        # Re-fetched every frame: the window surface is replaced on resize.
        target = self._window.get_surface()
        viewport = Viewport.fit(self.INTERNAL_SIZE, target.get_size())
        target.fill(self.BAR_COLOUR)
        # pygame.transform.scale is nearest-neighbour — never smoothscale here.
        target.blit(pygame.transform.scale(self._buffer, viewport.size), viewport.offset)
        self._window.flip()
