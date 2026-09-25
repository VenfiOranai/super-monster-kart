import numpy as np


class Mode7Plane:
    """A square, power-of-two track texture that repeats outside its bounds."""

    def __init__(self, texels: np.ndarray) -> None:
        width, height = texels.shape
        if width != height or width & (width - 1):
            raise ValueError(f"texture must be square and power-of-two, got {texels.shape}")
        self.size = width
        self._mask = width - 1
        self._flat = np.ascontiguousarray(texels).ravel()

    @property
    def dtype(self) -> np.dtype:
        return self._flat.dtype

    def sample(self, xs: np.ndarray, ys: np.ndarray) -> np.ndarray:
        """Nearest texel at each world coordinate, wrapping at the edges."""
        ix = np.floor(xs).astype(np.int32) & self._mask
        iy = np.floor(ys).astype(np.int32) & self._mask
        return self._flat[ix * self.size + iy]
