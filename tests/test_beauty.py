"""Milestone E: beauty/portrait algorithms (offline)."""
import numpy as np

from photostudio.imaging import beauty


def _portrait():
    # Noisy image so smoothing has a measurable effect; full alpha.
    rng = np.random.default_rng(0)
    img = rng.integers(60, 200, (80, 80, 4), dtype=np.uint8)
    img[..., 3] = 255
    return img


def test_skin_smooth_reduces_local_variance():
    img = _portrait()
    out = beauty.skin_smooth(img, 0.8)
    assert out.shape == img.shape
    assert np.std(out[..., :3].astype(float)) <= np.std(img[..., :3].astype(float))
    assert np.array_equal(out[..., 3], img[..., 3])


def test_skin_smooth_zero_is_noop():
    img = _portrait()
    assert np.array_equal(beauty.skin_smooth(img, 0.0), img)


def test_enhance_preserves_shape_and_alpha():
    img = _portrait()
    out = beauty.enhance_portrait(img, 0.6)
    assert out.shape == img.shape and out.dtype == np.uint8
    assert np.array_equal(out[..., 3], img[..., 3])


def test_heal_changes_region_only_near_point():
    img = np.full((60, 60, 4), 150, np.uint8)
    img[30, 30, :3] = [255, 0, 0]  # a red spot
    out = beauty.heal(img, 30, 30, radius=6)
    assert out.shape == img.shape
    # The spot is blended away (no longer pure red).
    assert not np.array_equal(out[30, 30, :3], np.array([255, 0, 0], np.uint8))
    # A far corner is unchanged.
    assert np.array_equal(out[5, 5], img[5, 5])


def test_background_blur_keeps_alpha_and_shape():
    img = _portrait()
    out = beauty.background_blur(img, 0.7)
    assert out.shape == img.shape
    assert np.array_equal(out[..., 3], img[..., 3])


def test_beauty_filters_registry_callable():
    img = _portrait()
    for name, (func, kwargs) in beauty.BEAUTY_FILTERS.items():
        out = func(img, **kwargs)
        assert out.shape == img.shape
