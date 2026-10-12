"""Geometric transforms on RGBA uint8 ndarrays. No Qt imports.

Crop/rotate/flip/resize. Rotations by multiples of 90 are lossless; arbitrary
rotation uses OpenCV with an expanded canvas and transparent fill.
"""
from __future__ import annotations

import cv2
import numpy as np


def _check(pixels: np.ndarray) -> None:
    if pixels.ndim != 3 or pixels.shape[2] != 4 or pixels.dtype != np.uint8:
        raise ValueError("expected H x W x 4 uint8 RGBA")


def crop(pixels: np.ndarray, x: int, y: int, width: int, height: int) -> np.ndarray:
    """Crop to the rectangle, clamped to image bounds. Returns a copy."""
    _check(pixels)
    h, w = pixels.shape[:2]
    x0 = max(0, min(int(x), w))
    y0 = max(0, min(int(y), h))
    x1 = max(x0, min(int(x) + int(width), w))
    y1 = max(y0, min(int(y) + int(height), h))
    if x1 - x0 < 1 or y1 - y0 < 1:
        raise ValueError("crop rectangle is empty after clamping")
    return pixels[y0:y1, x0:x1].copy()


def flip_horizontal(pixels: np.ndarray) -> np.ndarray:
    _check(pixels)
    return pixels[:, ::-1].copy()


def flip_vertical(pixels: np.ndarray) -> np.ndarray:
    _check(pixels)
    return pixels[::-1, :].copy()


def rotate_90(pixels: np.ndarray, turns: int = 1) -> np.ndarray:
    """Lossless rotation by multiples of 90 degrees. turns>0 = clockwise."""
    _check(pixels)
    # np.rot90 is counter-clockwise, so negate for clockwise-positive semantics.
    return np.rot90(pixels, k=(-turns) % 4).copy()


def resize(pixels: np.ndarray, width: int, height: int) -> np.ndarray:
    _check(pixels)
    if width < 1 or height < 1:
        raise ValueError("resize dimensions must be >= 1")
    interp = cv2.INTER_AREA if (width * height) < (pixels.shape[1] * pixels.shape[0]) \
        else cv2.INTER_CUBIC
    return cv2.resize(pixels, (int(width), int(height)), interpolation=interp)


def rotate_arbitrary(pixels: np.ndarray, degrees: float) -> np.ndarray:
    """Rotate by an arbitrary angle, expanding the canvas; new area is transparent."""
    _check(pixels)
    if degrees % 360 == 0:
        return pixels.copy()
    h, w = pixels.shape[:2]
    center = (w / 2.0, h / 2.0)
    mat = cv2.getRotationMatrix2D(center, degrees, 1.0)
    cos, sin = abs(mat[0, 0]), abs(mat[0, 1])
    new_w = int(h * sin + w * cos)
    new_h = int(h * cos + w * sin)
    mat[0, 2] += (new_w / 2.0) - center[0]
    mat[1, 2] += (new_h / 2.0) - center[1]
    return cv2.warpAffine(
        pixels, mat, (new_w, new_h),
        flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT,
        borderValue=(0, 0, 0, 0),
    )
