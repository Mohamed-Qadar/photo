import numpy as np
import pytest

from photostudio.imaging import transforms as tf


def test_crop_dimensions(rgba_gradient):
    out = tf.crop(rgba_gradient, 10, 5, 20, 15)
    assert out.shape == (15, 20, 4)


def test_crop_clamps_to_bounds(rgba_gradient):
    h, w = rgba_gradient.shape[:2]
    out = tf.crop(rgba_gradient, w - 5, h - 5, 100, 100)
    assert out.shape == (5, 5, 4)


def test_crop_empty_raises(rgba_gradient):
    with pytest.raises(ValueError):
        tf.crop(rgba_gradient, 1000, 1000, 10, 10)


def test_rotate_90_swaps_dims(rgba_gradient):
    out = tf.rotate_90(rgba_gradient, 1)
    assert out.shape[0] == rgba_gradient.shape[1]
    assert out.shape[1] == rgba_gradient.shape[0]


def test_rotate_90_four_turns_identity(rgba_gradient):
    out = tf.rotate_90(rgba_gradient, 4)
    assert np.array_equal(out, rgba_gradient)


def test_flip_horizontal_involution(rgba_gradient):
    assert np.array_equal(tf.flip_horizontal(tf.flip_horizontal(rgba_gradient)),
                          rgba_gradient)


def test_resize(rgba_gradient):
    out = tf.resize(rgba_gradient, 32, 24)
    assert out.shape == (24, 32, 4)


def test_rotate_arbitrary_expands_canvas(rgba_gradient):
    out = tf.rotate_arbitrary(rgba_gradient, 45)
    assert out.shape[0] > rgba_gradient.shape[0]
    assert out.shape[2] == 4
