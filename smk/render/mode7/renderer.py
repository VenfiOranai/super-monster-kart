import numpy as np

from smk.render.mode7.camera import Mode7Camera
from smk.render.mode7.plane import Mode7Plane


class Mode7Renderer:
    """Draws the plane into the rows of a buffer below the camera's horizon."""

    def __init__(self, plane: Mode7Plane, screen_size: tuple[int, int]) -> None:
        self._plane = plane
        self._width, self._height = screen_size
        # Pixel-centre offset of each column from the screen centre, as a column vector.
        self._columns = (np.arange(self._width, dtype=np.float32) + 0.5 - self._width / 2)[:, None]

    def world_coordinates(self, camera: Mode7Camera) -> tuple[np.ndarray, np.ndarray]:
        """World x and y sampled by every pixel below the horizon, each shaped (width, rows)."""
        focal = camera.focal_length(self._width)
        rows_below = np.arange(self._height - camera.horizon_y, dtype=np.float32) + 0.5
        scale = (camera.height / rows_below)[None, :]  # world units per pixel on that row
        distance = scale * focal
        forward_x, forward_y = camera.forward
        right_x, right_y = camera.right
        lateral = self._columns * scale
        xs = camera.x + forward_x * distance + right_x * lateral
        ys = camera.y + forward_y * distance + right_y * lateral
        return xs, ys

    def render(self, camera: Mode7Camera, pixels: np.ndarray) -> None:
        """Fill ``pixels[:, horizon_y:]``; rows above the horizon are left alone."""
        xs, ys = self.world_coordinates(camera)
        pixels[:, camera.horizon_y :] = self._plane.sample(xs, ys)
