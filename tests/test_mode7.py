import math

import numpy as np
import pytest

from smk.render.mode7 import Mode7Camera, Mode7Plane, Mode7Renderer
from smk.render.mode7.renderer import RowPlan

SCREEN = (320, 180)


def coordinate_texture(size: int = 1024) -> np.ndarray:
    """Each texel encodes its own position, so a sample says where it came from."""
    x = np.arange(size)[:, None]
    y = np.arange(size)[None, :]
    rgb = np.stack(np.broadcast_arrays(x % 256, y % 256, (x // 256) * 16 + y // 256), axis=-1)
    return rgb.astype(np.uint8)


def decode(rgb: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    rgb = rgb.astype(np.int64)
    return rgb[..., 0] + (rgb[..., 2] // 16) * 256, rgb[..., 1] + (rgb[..., 2] % 16) * 256


def coordinate_plane(size: int = 1024) -> Mode7Plane:
    return Mode7Plane(coordinate_texture(size))


def renderer() -> Mode7Renderer:
    return Mode7Renderer(coordinate_plane(), SCREEN)


def striped_renderer() -> Mode7Renderer:
    """Black, with 2-texel white lines every 128 texels across the direction of travel (+x)."""
    texels = np.zeros((1024, 1024, 3), dtype=np.uint8)
    texels[np.arange(1024) % 128 < 2] = 255
    return Mode7Renderer(Mode7Plane(texels), SCREEN)


def test_focal_length_derives_from_fov():
    camera = Mode7Camera(0, 0, 0, fov_degrees=90)
    assert camera.focal_length(320) == pytest.approx(160)


def test_coordinates_cover_every_pixel_below_the_horizon():
    xs, ys = renderer().world_coordinates(Mode7Camera(512, 512, 0, horizon_y=70))
    assert xs.shape == ys.shape == (320, 110)


def test_bottom_centre_looks_straight_ahead():
    camera = Mode7Camera(512, 512, angle=0)
    xs, ys = renderer().world_coordinates(camera)
    centre = SCREEN[0] // 2
    assert xs[centre, -1] > camera.x
    assert ys[centre, -1] == pytest.approx(camera.y, abs=1)


def test_rows_nearer_the_horizon_sample_further_away():
    camera = Mode7Camera(512, 512, angle=0)
    xs, _ = renderer().world_coordinates(camera)
    distances = xs[SCREEN[0] // 2] - camera.x
    assert np.all(np.diff(distances) < 0)


def test_bottom_row_distance_matches_the_gdd_formula():
    camera = Mode7Camera(0, 0, angle=0, height=48, horizon_y=70)
    xs, _ = renderer().world_coordinates(camera)
    row_below = SCREEN[1] - camera.horizon_y - 0.5  # pixel centre of the last row
    expected = camera.height * camera.focal_length(SCREEN[0]) / row_below
    assert xs[:, -1].mean() == pytest.approx(expected, rel=1e-4)


def test_edge_columns_sit_at_half_the_fov():
    camera = Mode7Camera(0, 0, angle=0, fov_degrees=68)
    xs, ys = renderer().world_coordinates(camera)
    edge = math.degrees(math.atan2(ys[-1, -1], xs[-1, -1]))
    # The last pixel's centre is half a pixel inside the screen edge, which sits at exactly 34°.
    last_centre = math.degrees(math.atan((SCREEN[0] / 2 - 0.5) / camera.focal_length(SCREEN[0])))
    screen_edge = math.degrees(math.atan((SCREEN[0] / 2) / camera.focal_length(SCREEN[0])))
    assert edge == pytest.approx(last_centre, abs=1e-3)
    assert screen_edge == pytest.approx(34)


def test_screen_right_is_the_cameras_right():
    # Facing +x with y pointing down the texture, the right-hand side is +y.
    xs, ys = renderer().world_coordinates(Mode7Camera(512, 512, angle=0))
    assert ys[-1, -1] > ys[0, -1]


def test_quarter_turn_rotates_the_view():
    r = renderer()
    xs0, ys0 = r.world_coordinates(Mode7Camera(0, 0, angle=0))
    xs1, ys1 = r.world_coordinates(Mode7Camera(0, 0, angle=math.pi / 2))
    np.testing.assert_allclose(xs1, -ys0, atol=1e-2)
    np.testing.assert_allclose(ys1, xs0, atol=1e-2)


def test_render_leaves_rows_above_the_horizon_alone():
    pixels = np.full((*SCREEN, 3), 7, dtype=np.uint8)
    renderer().render(Mode7Camera(512, 512, 0, horizon_y=70), pixels)
    assert np.all(pixels[:, :70] == 7)
    assert not np.all(pixels[:, 70:] == 7)


def assert_texels_under(pixels: np.ndarray, xs: np.ndarray, ys: np.ndarray) -> None:
    """Each pixel shows the texel under its world coordinate, except where that sits a hair from a
    texel edge and float rounding may reasonably pick either side."""
    sampled_x, sampled_y = decode(pixels)
    decisive = (np.abs(xs - np.round(xs)) > 1e-3) & (np.abs(ys - np.round(ys)) > 1e-3)
    assert decisive.mean() > 0.99
    np.testing.assert_array_equal(sampled_x[decisive], (np.floor(xs).astype(np.int64) % 1024)[decisive])
    np.testing.assert_array_equal(sampled_y[decisive], (np.floor(ys).astype(np.int64) % 1024)[decisive])


def test_near_rows_are_nearest_neighbour_when_filtered():
    r = renderer()
    camera = Mode7Camera(100.25, 900.75, angle=1.1)
    pixels = np.zeros((*SCREEN, 3), dtype=np.uint8)
    r.render(camera, pixels)
    xs, ys = r.world_coordinates(camera)
    plan = r.plan(camera)
    near = np.flatnonzero((plan.counts == 1) & (plan.levels[plan.starts] == 0))
    assert len(near) >= 3
    assert_texels_under(pixels[:, camera.horizon_y + near], xs[:, near], ys[:, near])


@pytest.mark.parametrize("camera", [Mode7Camera(100.25, 900.75, angle=1.1), Mode7Camera(-5000.5, 3.3, angle=-2.0)])
def test_unfiltered_render_is_nearest_neighbour_everywhere(camera):
    r = renderer()
    r.sharp_span = math.inf
    pixels = np.zeros((*SCREEN, 3), dtype=np.uint8)
    r.render(camera, pixels)
    xs, ys = r.world_coordinates(camera)
    assert_texels_under(pixels[:, camera.horizon_y :], xs, ys)


def test_uniform_texture_renders_uniformly_at_every_distance():
    plane = Mode7Plane(np.full((64, 64, 3), (10, 200, 77), dtype=np.uint8))
    pixels = np.zeros((*SCREEN, 3), dtype=np.uint8)
    Mode7Renderer(plane, SCREEN).render(Mode7Camera(3.7, 11.2, 0.4), pixels)
    assert np.all(pixels[:, 70:] == (10, 200, 77))


def test_rows_covering_little_depth_stay_sharp():
    r = renderer()
    camera = Mode7Camera(0, 0, 0)
    depth = camera.height * camera.focal_length(SCREEN[0])
    rows = np.arange(SCREEN[1] - camera.horizon_y)
    span = depth / np.maximum(rows, 0.5) - depth / (rows + 1)
    plan = r.plan(camera)
    sharp = span <= r.sharp_span
    assert sharp.sum() > 20
    assert np.all(plan.counts[sharp] == 1)
    assert np.all(plan.levels[plan.starts[sharp]] == 0)
    assert np.all(plan.counts[~sharp][2:] > 1)  # beyond it, filtered (bar the top-level rows at the horizon)


def test_sharp_span_moves_where_filtering_starts():
    r = renderer()
    camera = Mode7Camera(0, 0, 0)
    sharp_rows = []
    for span in (0.0, 2.0, 4.0):
        r.sharp_span = span
        sharp_rows.append(int((r.plan(camera).counts == 1).sum()))
    assert sharp_rows[0] < sharp_rows[1] < sharp_rows[2]


def test_samples_in_a_row_are_at_most_one_texel_of_their_level_apart():
    """The property that stops distant detail popping in and out as the camera moves."""
    camera = Mode7Camera(0, 0, 0)
    plan = renderer().plan(camera)
    for start, count in zip(plan.starts, plan.counts):
        if count < 2:
            continue
        distances = plan.distances[start : start + count]
        texel = 2.0 ** plan.levels[start]
        assert np.all(plan.levels[start : start + count] == plan.levels[start])
        assert np.all(-np.diff(distances) <= texel * 1.0001)
    assert plan.counts.max() <= RowPlan.MAX_SAMPLES


def test_thin_distant_lines_fade_rather_than_flicker_when_driving_forward():
    def worst_frame_to_frame_change(r: Mode7Renderer) -> np.ndarray:
        previous, worst = None, 0
        for step in range(512):
            pixels = np.zeros((*SCREEN, 3), dtype=np.uint8)
            camera = Mode7Camera(step * 0.25, 512.0, angle=0.0)
            r.render(camera, pixels)
            # Rows far enough away that one covers well over the 2-texel line width.
            column = pixels[SCREEN[0] // 2, camera.horizon_y : camera.horizon_y + 50, 0].astype(int)
            if previous is not None:
                worst = np.maximum(worst, np.abs(column - previous))
            previous = column
        return worst

    filtered = striped_renderer()
    unfiltered = striped_renderer()
    unfiltered.sharp_span = math.inf
    assert worst_frame_to_frame_change(unfiltered).max() == 255  # the flicker this guards against
    # Filtered, a quarter-texel step moves a line at most halfway on or off a pixel.
    assert worst_frame_to_frame_change(filtered).max() < 255 / 2


def test_plane_wraps_out_of_range_texels():
    plane = coordinate_plane(8)
    xs, ys = decode(plane.unpack(plane.gather(np.array([-1, 8, -8]), np.array([-1, 0, 9]))))
    np.testing.assert_array_equal(xs, [7, 0, 0])
    np.testing.assert_array_equal(ys, [7, 0, 1])


def test_mip_chain_halves_down_to_one_texel():
    assert coordinate_plane(1024).level_count == 11


def test_each_mip_level_averages_the_one_below():
    texels = np.array([[[0, 0, 0], [100, 40, 255]], [[200, 40, 255], [100, 40, 255]]], dtype=np.uint8)
    plane = Mode7Plane(texels)
    np.testing.assert_array_equal(plane.unpack(plane.gather(np.array(1), np.array(0))), [200, 40, 255])
    np.testing.assert_array_equal(plane.unpack(plane.gather(np.array(0), np.array(0), levels=1)), [100, 30, 191])


def test_mip_levels_wrap_at_their_own_size():
    texels = np.zeros((4, 4, 3), dtype=np.uint8)
    texels[2:, :2] = 200  # one 2x2 block, which is texel (1, 0) of level 1
    plane = Mode7Plane(texels)
    sampled = plane.unpack(plane.gather(np.array([1, 3, 0]), np.array([0, 2, 0]), levels=1))
    np.testing.assert_array_equal(sampled[:, 0], [200, 200, 0])


def test_pack_and_unpack_average_sums():
    plane_type = Mode7Plane
    colours = np.array([[10, 20, 30], [30, 40, 51]], dtype=np.uint8)
    total = plane_type.pack(colours).sum()
    np.testing.assert_array_equal(plane_type.unpack(total, 2), [20, 30, 41])


@pytest.mark.parametrize("shape", [(1000, 1000, 3), (512, 1024, 3), (64, 64)])
def test_plane_requires_square_power_of_two_rgb(shape):
    with pytest.raises(ValueError):
        Mode7Plane(np.zeros(shape, dtype=np.uint8))
