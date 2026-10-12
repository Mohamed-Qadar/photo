"""Beauty / portrait algorithms — local, offline, OpenCV-based. No Qt.

These aim for natural results and never distort facial geometry: they only smooth,
heal, enhance tone, and blur the background approximately. No AI models required.
All functions take and return H x W x 4 uint8 RGBA and preserve the alpha channel.
"""
from __future__ import annotations

import cv2
import numpy as np


def _rgb_alpha(pixels):
    return pixels[..., :3], pixels[..., 3:4]


def skin_smooth(pixels: np.ndarray, intensity: float = 0.6) -> np.ndarray:
    """Edge-preserving smoothing (bilateral) blended by intensity 0..1.

    Keeps edges (eyes, lips, hair) sharp while softening skin texture.
    """
    intensity = float(np.clip(intensity, 0.0, 1.0))
    if intensity <= 0.0:
        return pixels.copy()
    rgb, alpha = _rgb_alpha(pixels)
    smoothed = cv2.bilateralFilter(rgb, d=9, sigmaColor=45, sigmaSpace=9)
    out = (rgb.astype(np.float32) * (1 - intensity)
           + smoothed.astype(np.float32) * intensity)
    out = np.clip(out, 0, 255).astype(np.uint8)
    return np.concatenate([out, alpha], axis=-1)


def enhance_portrait(pixels: np.ndarray, amount: float = 0.5) -> np.ndarray:
    """Gentle portrait polish: mild smoothing + slight brightness & warmth."""
    amount = float(np.clip(amount, 0.0, 1.0))
    out = skin_smooth(pixels, intensity=0.4 * amount)
    rgb, alpha = _rgb_alpha(out)
    rgb = rgb.astype(np.float32)
    rgb += 10.0 * amount                       # lift shadows slightly
    rgb[..., 0] += 6.0 * amount                # touch of warmth
    rgb = np.clip(rgb, 0, 255).astype(np.uint8)
    return np.concatenate([rgb, alpha], axis=-1)


def heal(pixels: np.ndarray, cx: int, cy: int, radius: int = 14) -> np.ndarray:
    """Remove a blemish/spot around (cx, cy) using inpainting (Telea)."""
    h, w = pixels.shape[:2]
    mask = np.zeros((h, w), dtype=np.uint8)
    cv2.circle(mask, (int(cx), int(cy)), max(1, int(radius)), 255, -1)
    rgb = pixels[..., :3].copy()
    healed = cv2.inpaint(rgb, mask, inpaintRadius=max(3, radius // 2),
                         flags=cv2.INPAINT_TELEA)
    out = pixels.copy()
    out[..., :3] = healed
    return out


def background_blur(pixels: np.ndarray, strength: float = 0.7) -> np.ndarray:
    """Approximate portrait background blur.

    Blurs the whole image, then keeps a feathered central ellipse (where the
    subject usually is) sharp. No segmentation model — a simple, offline
    approximation that works best for centred portraits.
    """
    strength = float(np.clip(strength, 0.0, 1.0))
    if strength <= 0.0:
        return pixels.copy()
    h, w = pixels.shape[:2]
    k = int(6 + strength * 24) | 1
    blurred = cv2.GaussianBlur(pixels, (k, k), 0)

    mask = np.zeros((h, w), dtype=np.float32)
    cv2.ellipse(mask, (w // 2, int(h * 0.45)),
                (int(w * 0.30), int(h * 0.42)), 0, 0, 360, 1.0, -1)
    mask = cv2.GaussianBlur(mask, (0, 0), sigmaX=min(w, h) * 0.06)[..., None]

    out = pixels.astype(np.float32) * mask + blurred.astype(np.float32) * (1 - mask)
    out = np.clip(out, 0, 255).astype(np.uint8)
    out[..., 3] = pixels[..., 3]
    return out


#: name -> (function, default kwargs) for the Beauty menu.
BEAUTY_FILTERS = {
    "Skin Smoothing": (skin_smooth, {"intensity": 0.6}),
    "Portrait Enhance": (enhance_portrait, {"amount": 0.5}),
    "Background Blur": (background_blur, {"strength": 0.7}),
}
