"""A generated placeholder track texture for renderer spikes and benchmarks.

Not a track. It is built so that errors in the transform are visible at a
glance: an 8×8 checker shows the tile grid and any shimmer, bright lines every
128 px show scale and straightness, and each quadrant has its own tint so a
mirrored or wrongly rotated plane is obvious.
"""

import numpy as np


class CalibrationTexture:
    TILE = 8
    GRID = 128
    LIGHT = 150
    DARK = 110
    GRID_COLOUR = (240, 240, 240)
    ORIGIN_COLOUR = (255, 0, 255)
    # Quadrant tints, indexed [x half][y half].
    TINTS = np.array(
        [
            [[1.0, 0.55, 0.55], [0.55, 1.0, 0.55]],
            [[0.55, 0.55, 1.0], [1.0, 1.0, 0.45]],
        ],
        dtype=np.float32,
    )

    @classmethod
    def generate(cls, size: int = 1024) -> np.ndarray:
        """An RGB array shaped (size, size, 3) and indexed [x, y] like pygame.surfarray."""
        coords = np.arange(size)
        x = coords[:, None]
        y = coords[None, :]

        checker = ((x // cls.TILE + y // cls.TILE) % 2).astype(bool)
        grey = np.where(checker, cls.LIGHT, cls.DARK).astype(np.float32)
        half_x = (x >= size // 2).astype(int)
        half_y = (y >= size // 2).astype(int)
        rgb = grey[..., None] * cls.TINTS[half_x, half_y]

        on_grid = (x % cls.GRID < 2) | (y % cls.GRID < 2)
        rgb[np.broadcast_to(on_grid, (size, size))] = cls.GRID_COLOUR
        rgb[: cls.TILE * 2, : cls.TILE * 2] = cls.ORIGIN_COLOUR
        return rgb.astype(np.uint8)
