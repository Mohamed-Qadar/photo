"""Spatial image filters (blur, sharpen) on RGBA uint8 arrays. No Qt."""
from __future__ import annotations

import cv2
import numpy as np


def gaussian_blur(pixels: np.ndarray, radius: float = 3.0) -> np.ndarray:
    radius = max(0.1, float(radius))
    k = int(radius) * 2 + 1
    return cv2.GaussianBlur(pixels, (k, k), radius)


def sharpen(pixels: np.ndarray, amount: float = 1.0) -> np.ndarray:
    """Unsharp mask. amount>0 sharpens."""
    blurred = cv2.GaussianBlur(pixels.astype(np.float32), (0, 0), 2.0)
    out = pixels.astype(np.float32) * (1.0 + amount) - blurred * amount
    out[..., 3] = pixels[..., 3]  # keep alpha intact
    return np.clip(out, 0, 255).astype(np.uint8)


#: name -> (function, default kwargs) for the Filter menu.
FILTERS = {
    "Gaussian Blur": (gaussian_blur, {"radius": 4.0}),
    "Sharpen": (sharpen, {"amount": 1.0}),
}
