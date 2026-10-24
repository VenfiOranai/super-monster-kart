"""The simulation's only source of randomness (GDD §14.8)."""

_MASK_64 = (1 << 64) - 1


class Rng:
    """A seeded SplitMix64 generator whose whole state is one integer.

    SplitMix64 is fully specified here rather than borrowed from ``random``, so
    the sequence is the same on every platform and Python version, and the
    state can be hashed into a snapshot or sent over the wire as-is.
    """

    def __init__(self, seed: int) -> None:
        self._state = seed & _MASK_64

    @property
    def state(self) -> int:
        return self._state

    def next_u64(self) -> int:
        self._state = (self._state + 0x9E3779B97F4A7C15) & _MASK_64
        z = self._state
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & _MASK_64
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & _MASK_64
        return z ^ (z >> 31)

    def random(self) -> float:
        """A float in [0, 1), from the top 53 bits so every value is exact."""
        return (self.next_u64() >> 11) * 2.0**-53

    def uniform(self, low: float, high: float) -> float:
        """A float in [low, high)."""
        return low + (high - low) * self.random()
