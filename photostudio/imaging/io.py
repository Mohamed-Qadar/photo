"""Image load/save via Pillow, normalized to/from RGBA uint8 ndarrays.

Supported imports: JPG, PNG, WebP, TIFF. Exports: PNG, JPG (Phase 1).
No Qt imports.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

READ_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp"}


def load_image(path: str | Path) -> np.ndarray:
    """Load any supported image as H x W x 4 uint8 RGBA."""
    path = Path(path)
    with Image.open(path) as img:
        img = img.convert("RGBA")
        return np.asarray(img, dtype=np.uint8).copy()


def save_png(pixels: np.ndarray, path: str | Path, keep_alpha: bool = True) -> None:
    img = Image.fromarray(pixels, mode="RGBA")
    if not keep_alpha:
        bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
        img = Image.alpha_composite(bg, img).convert("RGB")
    img.save(Path(path), format="PNG")


def save_jpg(pixels: np.ndarray, path: str | Path, quality: int = 92,
             background: tuple[int, int, int] = (255, 255, 255)) -> None:
    """JPG has no alpha; composite over a solid background first."""
    img = Image.fromarray(pixels, mode="RGBA")
    bg = Image.new("RGBA", img.size, (*background, 255))
    flat = Image.alpha_composite(bg, img).convert("RGB")
    flat.save(Path(path), format="JPEG", quality=int(np.clip(quality, 1, 100)))
