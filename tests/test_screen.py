import pytest

from smk.render.screen import Screen, Viewport


@pytest.mark.parametrize(
    ("window", "scale"),
    [
        ((1280, 720), 4),
        ((1920, 1080), 6),
        ((2560, 1440), 8),
        ((3840, 2160), 12),
    ],
)
def test_common_displays_scale_exactly(window, scale):
    viewport = Viewport.fit(Screen.INTERNAL_SIZE, window)
    assert viewport.scale == scale
    assert viewport.size == window
    assert viewport.offset == (0, 0)


def test_awkward_window_uses_integer_scale_and_centres():
    viewport = Viewport.fit(Screen.INTERNAL_SIZE, (1000, 700))
    assert viewport.scale == 3
    assert viewport.size == (960, 540)
    assert viewport.offset == (20, 80)


def test_ultrawide_gets_pillarbox_not_wider_view():
    viewport = Viewport.fit(Screen.INTERNAL_SIZE, (3440, 1440))
    assert viewport.scale == 8
    assert viewport.size == (2560, 1440)
    assert viewport.offset == (440, 0)


@pytest.mark.parametrize(
    ("desktop", "window"),
    [
        ((1920, 1080), (1280, 720)),
        ((2560, 1440), (1920, 1080)),
        ((3840, 2160), (2880, 1620)),
        ((1366, 768), (960, 540)),
    ],
)
def test_default_window_is_an_exact_scale_with_room_to_spare(desktop, window):
    assert Screen.default_window_size(desktop) == window
