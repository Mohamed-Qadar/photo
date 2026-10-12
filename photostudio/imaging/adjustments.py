"""Non-destructive tone adjustments applied to RGBA ndarrays.

Each function takes and returns H x W x 4 uint8 RGBA. Alpha is preserved.
Math is done in float32 and clipped back to uint8. Neutral params return an
unchanged copy. Phase 1 ships brightness + contrast; later phases extend this
module (exposure, saturation, white balance, curves, ...).
"""
from __future__ import annotations

import numpy as np


def _split(pixels: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    rgb = pixels[..., :3].astype(np.float32)
    alpha = pixels[..., 3:4]
    return rgb, alpha


def _finish(rgb: np.ndarray, alpha: np.ndarray) -> np.ndarray:
    rgb = np.clip(rgb, 0.0, 255.0).astype(np.uint8)
    return np.concatenate([rgb, alpha], axis=-1)


def brightness(pixels: np.ndarray, amount: float) -> np.ndarray:
    """amount in [-1, 1]; 0 is neutral. +1 adds ~128 levels, -1 subtracts ~128."""
    if amount == 0.0:
        return pixels.copy()
    rgb, alpha = _split(pixels)
    rgb = rgb + float(amount) * 128.0
    return _finish(rgb, alpha)


def contrast(pixels: np.ndarray, amount: float) -> np.ndarray:
    """amount in [-1, 1]; 0 is neutral. Scales RGB around mid-gray (128)."""
    if amount == 0.0:
        return pixels.copy()
    rgb, alpha = _split(pixels)
    factor = 1.0 + float(amount)          # -1 -> 0 (flat gray), +1 -> 2x
    rgb = (rgb - 128.0) * factor + 128.0
    return _finish(rgb, alpha)


_LUMA = np.array([0.299, 0.587, 0.114], dtype=np.float32)


def exposure(pixels: np.ndarray, amount: float) -> np.ndarray:
    """amount in [-1, 1]; multiplicative, ~±2 stops at the extremes."""
    if amount == 0.0:
        return pixels.copy()
    rgb, alpha = _split(pixels)
    rgb = rgb * (2.0 ** (float(amount) * 2.0))
    return _finish(rgb, alpha)


def saturation(pixels: np.ndarray, amount: float) -> np.ndarray:
    """amount in [-1, 1]; -1 = grayscale, 0 = neutral, +1 = doubled saturation."""
    if amount == 0.0:
        return pixels.copy()
    rgb, alpha = _split(pixels)
    gray = (rgb * _LUMA).sum(axis=-1, keepdims=True)
    rgb = gray + (rgb - gray) * (1.0 + float(amount))
    return _finish(rgb, alpha)


def temperature(pixels: np.ndarray, amount: float) -> np.ndarray:
    """amount in [-1, 1]; warm (+) raises red / lowers blue, cool (-) the reverse."""
    if amount == 0.0:
        return pixels.copy()
    rgb, alpha = _split(pixels)
    shift = float(amount) * 40.0
    rgb[..., 0] += shift
    rgb[..., 2] -= shift
    return _finish(rgb, alpha)


def grayscale(pixels: np.ndarray, amount: float) -> np.ndarray:
    """amount in [0, 1]; mixes the image toward its luma."""
    if amount <= 0.0:
        return pixels.copy()
    rgb, alpha = _split(pixels)
    gray = (rgb * _LUMA).sum(axis=-1, keepdims=True)
    rgb = rgb * (1.0 - float(amount)) + gray * float(amount)
    return _finish(rgb, alpha)


#: Registry so the pipeline/UI can iterate adjustments generically.
#: Order matters — this is the application order in apply_adjustments.
ADJUSTMENTS = {
    "exposure": exposure,
    "brightness": brightness,
    "contrast": contrast,
    "temperature": temperature,
    "saturation": saturation,
    "grayscale": grayscale,
}


def apply_adjustments(pixels: np.ndarray, params: dict[str, float]) -> np.ndarray:
    """Apply all known adjustments in a defined order. Unknown keys are ignored."""
    out = pixels
    first = True
    for key, func in ADJUSTMENTS.items():
        value = float(params.get(key, 0.0))
        if value == 0.0:
            continue
        out = func(out, value)
        first = False
    return out if not first else pixels.copy()
