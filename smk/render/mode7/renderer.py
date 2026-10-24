from dataclasses import dataclass

import numpy as np

from smk import consts
from smk.render.mode7.camera import Mode7Camera
from smk.render.mode7.plane import Mode7Plane


@dataclass(frozen=True, eq=False)
class RowPlan:
    """Where each row below the horizon samples the plane, and from which mip level.

    A row far from the camera covers many texels of depth. Sampling it once
    lets thin features pop in and out as the camera moves forward, so each
    row instead takes up to ``MAX_SAMPLES`` evenly spaced samples across the
    depth it covers and averages them. The samples come from the mip level at
    which neighbouring samples are at most one texel apart.

    Rows covering no more than ``sharp_span`` texels of depth are left sharp:
    one level-0 sample at the pixel centre, which is plain nearest-neighbour.
    A feature at least ``sharp_span`` texels deep can't fall between those
    samples, so it can't flicker. An infinite ``sharp_span`` turns filtering
    off. The plan depends only on the camera's height, horizon and FOV.
    """

    MAX_SAMPLES = consts.MAX_DISTANCE_SAMPLES

    distances: np.ndarray  # (samples,) camera distance of each sample
    levels: np.ndarray  # (samples,) mip level of each sample
    starts: np.ndarray  # (rows,) index of each row's first sample
    counts: np.ndarray  # (rows,) samples in each row

    @classmethod
    def build(
        cls, camera: Mode7Camera, screen_size: tuple[int, int], max_level: int, sharp_span: float
    ) -> "RowPlan":
        """``max_level`` is the plane's top mip level, which is a single texel."""
        width, height = screen_size
        focal = camera.focal_length(width)
        depth = camera.height * focal  # distance = depth / rows below the horizon
        rows = np.arange(height - camera.horizon_y, dtype=np.float64)
        # Row i spans [i, i + 1] rows below the horizon. The horizon itself is
        # infinitely far away, so the top row stops half a row short of it.
        far = depth / np.maximum(rows, 0.5)
        near = depth / (rows + 1)
        centre = depth / (rows + 0.5)
        span = far - near  # depth the row covers, in texels

        lateral_level = np.round(np.log2(np.maximum(centre / focal, 1.0)))  # texels per column
        depth_level = np.ceil(np.log2(np.maximum(span / cls.MAX_SAMPLES, 1.0)))
        levels = np.clip(np.maximum(lateral_level, depth_level), 0, max_level).astype(np.int32)
        counts = np.clip(np.ceil(span / np.exp2(levels)), 1, cls.MAX_SAMPLES).astype(np.int32)
        counts[levels == max_level] = 1  # a single texel; more samples would all match
        sharp = span <= sharp_span
        levels[sharp] = 0
        counts[sharp] = 1
        starts = np.concatenate(([0], np.cumsum(counts)[:-1]))

        row_of = np.repeat(np.arange(len(rows)), counts)
        within = np.arange(counts.sum()) - starts[row_of]
        spread = far[row_of] - (within + 0.5) / counts[row_of] * span[row_of]
        distances = np.where(counts[row_of] == 1, centre[row_of], spread)
        return cls(distances.astype(np.float32), levels[row_of], starts, counts)


class Mode7Renderer:
    """Draws the plane into the rows of a buffer below the camera's horizon.

    Distant rows are filtered across the depth they cover (see ``RowPlan``).
    ``sharp_span`` sets where that starts; ``math.inf`` turns it off, leaving
    every pixel a single nearest-neighbour sample.
    """

    def __init__(self, plane: Mode7Plane, screen_size: tuple[int, int]) -> None:
        if not 1 <= RowPlan.MAX_SAMPLES <= Mode7Plane.MAX_SUMMED:
            raise ValueError(f"MAX_DISTANCE_SAMPLES must be 1 to {Mode7Plane.MAX_SUMMED}, got {RowPlan.MAX_SAMPLES}")
        self._plane = plane
        self._size = screen_size
        self._width, self._height = screen_size
        self.sharp_span = consts.SHARP_SPAN
        # Pixel-centre offset of each column from the screen centre, as a row vector.
        self._columns = (np.arange(self._width, dtype=np.float32) + 0.5 - self._width / 2)[None, :]
        self._plan_key: tuple | None = None
        self._plan: RowPlan | None = None
        self._inverse_texels: np.ndarray | None = None
        self._margins: np.ndarray | None = None

    def plan(self, camera: Mode7Camera) -> RowPlan:
        """The row plan for this camera, rebuilt only when height, horizon, FOV or ``sharp_span`` change."""
        key = (camera.height, camera.horizon_y, camera.fov_degrees, self.sharp_span)
        if key != self._plan_key:
            self._plan = RowPlan.build(camera, self._size, self._plane.level_count - 1, self.sharp_span)
            self._plan_key = key
            self._prepare_texel_coordinates(camera, self._plan)
        return self._plan

    def world_coordinates(self, camera: Mode7Camera) -> tuple[np.ndarray, np.ndarray]:
        """World x and y at the centre of every pixel below the horizon, each shaped (width, rows).

        The GDD §14.4 transform written plainly. ``render`` uses a faster
        equivalent (``_texel_coordinates``); tests check one against the other.
        """
        focal = camera.focal_length(self._width)
        distances = camera.height * focal / (np.arange(self._height - camera.horizon_y, dtype=np.float32) + 0.5)
        lateral = self._columns * (distances / focal)[:, None]
        forward_x, forward_y = camera.forward
        right_x, right_y = camera.right
        xs = camera.x + forward_x * distances[:, None] + right_x * lateral
        ys = camera.y + forward_y * distances[:, None] + right_y * lateral
        return xs.T, ys.T

    def render(self, camera: Mode7Camera, pixels: np.ndarray) -> None:
        """Fill ``pixels[:, horizon_y:]`` with RGB; rows above the horizon are left alone.

        ``pixels`` is RGB indexed ``[x, y, channel]``, like ``pygame.surfarray.pixels3d``.
        """
        plan = self.plan(camera)
        us, vs = self._texel_coordinates(camera, plan)
        samples = self._plane.gather(us.astype(np.int32), vs.astype(np.int32), plan.levels[:, None])
        sums = np.add.reduceat(samples, plan.starts, axis=0)
        pixels[:, camera.horizon_y :] = self._plane.unpack(sums, plan.counts[:, None]).transpose(1, 0, 2)

    def _prepare_texel_coordinates(self, camera: Mode7Camera, plan: RowPlan) -> None:
        """Per-sample constants for ``_texel_coordinates``, rebuilt with the plan they belong to."""
        level_sizes = self._plane.size >> plan.levels
        self._inverse_texels = np.exp2(-plan.levels).astype(np.float32)  # that level's texels per level-0 texel
        # The furthest a sample can reach behind the wrapped camera, straight
        # ahead plus half a screen sideways, rounded up to whole texture repeats.
        reach = plan.distances * (1 + self._width / 2 / camera.focal_length(self._width)) * self._inverse_texels
        self._margins = (np.ceil(reach / level_sizes + 1) * level_sizes).astype(np.float32)

    def _texel_coordinates(self, camera: Mode7Camera, plan: RowPlan) -> tuple[np.ndarray, np.ndarray]:
        """Where each sample lands, in its own level's texels, shaped (samples, width).

        Equivalent to ``world_coordinates`` at the plan's distances, divided by
        each level's texel size, but about twice as fast: each axis is one
        multiply-add, and the work is row-major to match the surface's memory.
        The camera is wrapped onto the texture and each sample shifted by whole
        texture repeats, so every coordinate is non-negative and truncating to
        an integer is flooring.
        """
        size = self._plane.size
        forward_x, forward_y = camera.forward
        right_x, right_y = camera.right
        ahead = plan.distances * self._inverse_texels
        across = ahead / camera.focal_length(self._width)  # per column
        base_x = (camera.x % size) * self._inverse_texels + forward_x * ahead + self._margins
        base_y = (camera.y % size) * self._inverse_texels + forward_y * ahead + self._margins
        us = self._columns * (right_x * across)[:, None] + base_x[:, None]
        vs = self._columns * (right_y * across)[:, None] + base_y[:, None]
        return us, vs
