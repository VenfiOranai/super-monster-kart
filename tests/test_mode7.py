import math

import numpy as np
import pytest

from smk.render.mode7 import Mode7Camera, Mode7Plane, Mode7Renderer

SCREEN = (320, 180)


def coordinate_plane(size: int = 1024) -> Mode7Plane:
    """Each texel stores its own x * size + y, so a sample says where it came from."""
    return Mode7Plane(np.arange(size * size, dtype=np.uint32).reshape(size, size))


def renderer() -> Mode7Renderer:
    return Mode7Renderer(coordinate_plane(), SCREEN)


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
    pixels = np.full(SCREEN, 7, dtype=np.uint32)
    renderer().render(Mode7Camera(512, 512, 0, horizon_y=70), pixels)
    assert np.all(pixels[:, :70] == 7)
    assert not np.all(pixels[:, 70:] == 7)


def test_render_samples_the_texel_under_each_coordinate():
    r = renderer()
    camera = Mode7Camera(100.25, 900.75, angle=1.1)
    pixels = np.zeros(SCREEN, dtype=np.uint32)
    r.render(camera, pixels)
    xs, ys = r.world_coordinates(camera)
    expected = (np.floor(xs).astype(np.int64) % 1024) * 1024 + np.floor(ys).astype(np.int64) % 1024
    np.testing.assert_array_equal(pixels[:, camera.horizon_y :], expected)


def test_plane_wraps_negative_coordinates():
    plane = coordinate_plane(8)
    sampled = plane.sample(np.array([-0.5, 8.0, -8.0]), np.array([-0.5, 0.0, 9.5]))
    np.testing.assert_array_equal(sampled, [7 * 8 + 7, 0, 1])


@pytest.mark.parametrize("shape", [(1000, 1000), (512, 1024)])
def test_plane_requires_square_power_of_two(shape):
    with pytest.raises(ValueError):
        Mode7Plane(np.zeros(shape, dtype=np.uint32))

