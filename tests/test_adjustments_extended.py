"""Milestone B: extended adjustments + spatial filters."""
import numpy as np
import pytest

from photostudio.imaging import adjustments as adj
from photostudio.imaging import filters


@pytest.fixture
def mid():
    img = np.zeros((20, 20, 4), dtype=np.uint8)
    img[..., 0] = 200
    img[..., 1] = 100
    img[..., 2] = 50
    img[..., 3] = 255
    return img


def test_exposure_brightens(mid):
    out = adj.exposure(mid, 0.5)
    assert out[..., :3].mean() > mid[..., :3].mean()
    assert np.array_equal(out[..., 3], mid[..., 3])


def test_saturation_minus_one_is_gray(mid):
    out = adj.saturation(mid, -1.0)
    r, g, b = out[0, 0, 0], out[0, 0, 1], out[0, 0, 2]
    assert abs(int(r) - int(g)) <= 1 and abs(int(g) - int(b)) <= 1


def test_temperature_warm_raises_red(mid):
    warm = adj.temperature(mid, 0.5)
    assert warm[0, 0, 0] >= mid[0, 0, 0]
    assert warm[0, 0, 2] <= mid[0, 0, 2]


def test_grayscale_full(mid):
    out = adj.grayscale(mid, 1.0)
    assert out[0, 0, 0] == out[0, 0, 1] == out[0, 0, 2]


def test_grayscale_zero_is_noop(mid):
    assert np.array_equal(adj.grayscale(mid, 0.0), mid)


def test_apply_adjustments_combined_preserves_alpha_and_shape(mid):
    out = adj.apply_adjustments(mid, {"exposure": 0.2, "saturation": 0.3,
                                      "temperature": -0.2, "grayscale": 0.0})
    assert out.shape == mid.shape and out.dtype == np.uint8
    assert np.array_equal(out[..., 3], mid[..., 3])


def test_blur_and_sharpen_keep_shape_and_alpha(mid):
    b = filters.gaussian_blur(mid, 3.0)
    s = filters.sharpen(mid, 1.0)
    assert b.shape == mid.shape and s.shape == mid.shape
    assert np.array_equal(b[..., 3], mid[..., 3])
    assert np.array_equal(s[..., 3], mid[..., 3])


def test_before_after_composite_differs():
    from photostudio.core.document import Document
    from photostudio.core.pipeline import composite
    doc = Document.from_image(np.full((10, 10, 4), 100, np.uint8))
    doc.active_layer.adjustments["exposure"] = 0.5
    after = composite(doc, use_adjustments=True)
    before = composite(doc, use_adjustments=False)
    assert after[..., :3].mean() > before[..., :3].mean()


def test_filter_command_undo():
    from photostudio.core.document import Document
    from photostudio.core.history import History
    from photostudio.core import commands
    doc = Document.from_image(np.random.randint(0, 255, (16, 16, 4), np.uint8))
    layer = doc.active_layer
    original = layer.pixels.copy()
    hist = History()
    hist.push(commands.FilterCommand(doc, layer, filters.gaussian_blur,
                                     "Gaussian Blur", radius=3.0))
    assert not np.array_equal(layer.pixels, original)
    hist.undo()
    assert np.array_equal(layer.pixels, original)
