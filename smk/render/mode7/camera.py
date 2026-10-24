import math
from dataclasses import dataclass

from smk import consts


@dataclass(frozen=True)
class Mode7Camera:
    """Where the plane is viewed from. Texture-space coordinates; see the package docstring."""

    x: float
    y: float
    angle: float
    height: float = consts.CAMERA_HEIGHT
    horizon_y: int = consts.HORIZON_Y
    fov_degrees: float = consts.FOV_DEGREES

    def focal_length(self, screen_width: int) -> float:
        """Derived from the authored FOV, never the reverse (GDD §12.3)."""
        return (screen_width / 2) / math.tan(math.radians(self.fov_degrees) / 2)

    @property
    def forward(self) -> tuple[float, float]:
        return math.cos(self.angle), math.sin(self.angle)

    @property
    def right(self) -> tuple[float, float]:
        return -math.sin(self.angle), math.cos(self.angle)
