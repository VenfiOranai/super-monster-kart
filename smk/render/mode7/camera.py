import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Mode7Camera:
    """Where the plane is viewed from. Texture-space coordinates; see the package docstring."""

    x: float
    y: float
    angle: float
    height: float = 48.0  # CAM_HEIGHT, GDD §12.3
    horizon_y: int = 70
    fov_degrees: float = 68.0  # GDD §12.3

    def focal_length(self, screen_width: int) -> float:
        """Derived from the authored FOV, never the reverse (GDD §12.3)."""
        return (screen_width / 2) / math.tan(math.radians(self.fov_degrees) / 2)

    @property
    def forward(self) -> tuple[float, float]:
        return math.cos(self.angle), math.sin(self.angle)

    @property
    def right(self) -> tuple[float, float]:
        return -math.sin(self.angle), math.cos(self.angle)
