"""One tick of controls for one racer (GDD §11.1).

Humans and AI both produce these; the simulation cannot tell them apart.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class InputFrame:
    """The buttons and stick for a single racer on a single tick.

    The default is no input at all: coasting, wheel centred.
    """

    throttle: bool = False
    brake: bool = False
    steer: float = 0.0
    """-1 is full left, +1 full right."""
    hop: bool = False
    attack_1: bool = False
    attack_2: bool = False
    attack_3: bool = False
    rider_active: bool = False
    use_item: bool = False

    def __post_init__(self) -> None:
        if not -1.0 <= self.steer <= 1.0:
            raise ValueError(f"steer must be within [-1, 1], got {self.steer}")
