import numpy as np

from tools.calibration import CalibrationTexture


def test_calibration_texture_is_a_track_sized_rgb_image():
    texture = CalibrationTexture.generate()
    assert texture.shape == (1024, 1024, 3)
    assert texture.dtype == np.uint8


def test_calibration_quadrants_are_distinguishable():
    texture = CalibrationTexture.generate().astype(int)
    probes = [(40, 40), (40, 600), (600, 40), (600, 600)]  # off the grid lines
    tints = {tuple(np.sign(texture[x, y] - texture[x, y].mean())) for x, y in probes}
    assert len(tints) == 4
