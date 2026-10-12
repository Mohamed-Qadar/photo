import numpy as np

from photostudio.imaging import adjustments as adj


def test_brightness_neutral_returns_equal_copy(rgba_gradient):
    out = adj.brightness(rgba_gradient, 0.0)
    assert np.array_equal(out, rgba_gradient)
    assert out is not rgba_gradient


def test_brightness_increases_values(rgba_gradient):
    out = adj.brightness(rgba_gradient, 0.5)
    # RGB should increase (clipped), alpha unchanged
    assert out[..., :3].mean() > rgba_gradient[..., :3].mean()
    assert np.array_equal(out[..., 3], rgba_gradient[..., 3])


def test_brightness_clips(rgba_gradient):
    out = adj.brightness(rgba_gradient, 1.0)
    assert out.max() <= 255 and out.min() >= 0


def test_contrast_neutral(rgba_gradient):
    out = adj.contrast(rgba_gradient, 0.0)
    assert np.array_equal(out, rgba_gradient)


def test_contrast_flat_gray_at_minus_one(rgba_gradient):
    out = adj.contrast(rgba_gradient, -1.0)
    # factor 0 -> everything maps to 128 for RGB
    assert np.all(out[..., :3] == 128)


def test_apply_adjustments_preserves_alpha(rgba_gradient):
    out = adj.apply_adjustments(rgba_gradient, {"brightness": 0.2, "contrast": 0.3})
    assert np.array_equal(out[..., 3], rgba_gradient[..., 3])
    assert out.dtype == np.uint8
