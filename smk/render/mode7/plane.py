import numpy as np


class Mode7Plane:
    """A square, power-of-two RGB track texture with a box-filtered mip chain.

    Level 0 is the texture itself; each level above it halves the size by
    averaging 2×2 texels, down to 1×1. Every level repeats outside its bounds.

    Texels are stored packed as ``r | g << 10 | b << 20`` in a uint32, so one
    gather fetches a whole colour and up to ``MAX_SUMMED`` samples can be
    summed before a channel overflows into the next.
    """

    PACKED = np.uint32
    SHIFTS = np.array([0, 10, 20], dtype=np.uint32)
    CHANNEL_MASK = np.uint32(0x3FF)
    MAX_SUMMED = 4  # 4 * 255 fits the 10-bit channel

    def __init__(self, texels: np.ndarray) -> None:
        if texels.ndim != 3 or texels.shape[2] != 3:
            raise ValueError(f"texture must be RGB, shaped (size, size, 3), got {texels.shape}")
        width, height, _ = texels.shape
        if width != height or width & (width - 1):
            raise ValueError(f"texture must be square and power-of-two, got {texels.shape[:2]}")
        self.size = width

        levels = [texels.astype(np.uint16)]
        while levels[-1].shape[0] > 1:
            finer = levels[-1]
            summed = finer[0::2, 0::2] + finer[1::2, 0::2] + finer[0::2, 1::2] + finer[1::2, 1::2]
            levels.append((summed + 2) // 4)
        self.level_count = len(levels)
        self._offsets = np.cumsum([0] + [level.shape[0] ** 2 for level in levels[:-1]]).astype(np.int32)
        self._flat = np.concatenate([self.pack(level).ravel() for level in levels])

    @classmethod
    def pack(cls, rgb: np.ndarray) -> np.ndarray:
        """RGB (..., 3) to packed (...)."""
        return np.bitwise_or.reduce(rgb.astype(cls.PACKED) << cls.SHIFTS, axis=-1)

    @classmethod
    def unpack(cls, packed: np.ndarray, counts: np.ndarray | int = 1) -> np.ndarray:
        """Packed sums of ``counts`` samples to their rounded mean, as uint8 RGB (..., 3).

        ``counts`` broadcasts against ``packed`` and is at most ``MAX_SUMMED``.
        """
        packed = np.asarray(packed, dtype=cls.PACKED)
        reciprocal = 1 / np.asarray(counts, dtype=np.float32)
        rgb = np.empty((*packed.shape, 3), dtype=np.uint8)
        # One channel at a time: numpy is slow over a length-3 innermost axis.
        for channel, shift in enumerate(cls.SHIFTS):
            mean = ((packed >> shift) & cls.CHANNEL_MASK).astype(np.float32) * reciprocal
            rgb[..., channel] = mean + np.float32(0.5)
        return rgb

    def gather(self, ix: np.ndarray, iy: np.ndarray, levels: np.ndarray | int = 0) -> np.ndarray:
        """Packed colour of texel (ix, iy) of each level, in that level's texels, wrapping.

        ``levels`` broadcasts against ``ix`` and ``iy``.
        """
        levels = np.asarray(levels)
        sizes = (self.size >> levels).astype(np.int32)
        masks = sizes - 1
        return self._flat[self._offsets[levels] + (ix & masks) * sizes + (iy & masks)]
