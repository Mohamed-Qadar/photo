"""Passport / ID photo helpers: DPI math, background replacement and print sheets.

Pure Python + NumPy/OpenCV/Pillow. No Qt.

IMPORTANT: the photo-size presets below are common *examples* for layout and are
NOT a claim of any government's official biometric requirements. Users must verify
the exact size, background and composition required by the relevant authority.
Nothing here guarantees acceptance by any passport or ID office.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from PIL import Image


@dataclass(frozen=True)
class PhotoSize:
    key: str
    label: str
    width_mm: float
    height_mm: float


# Example layout sizes only — verify against the real requirement before use.
PHOTO_SIZES = [
    PhotoSize("35x45", "35 × 45 mm (common example)", 35, 45),
    PhotoSize("50x50", "50 × 50 mm (2×2 in example)", 50.8, 50.8),
    PhotoSize("40x60", "40 × 60 mm (example)", 40, 60),
]


@dataclass(frozen=True)
class SheetSize:
    key: str
    label: str
    width_mm: float
    height_mm: float


SHEET_SIZES = [
    SheetSize("10x15", "10 × 15 cm photo paper", 100, 150),
    SheetSize("a4", "A4 (210 × 297 mm)", 210, 297),
]


def mm_to_px(mm: float, dpi: int) -> int:
    """Convert millimetres to pixels at the given DPI (1 in = 25.4 mm)."""
    if not np.isfinite(mm) or mm <= 0 or dpi <= 0:
        raise ValueError("Physical dimensions and DPI must be positive")
    return max(1, int(round(mm / 25.4 * dpi)))


def replace_background(pixels: np.ndarray, new_color=(255, 255, 255),
                       tolerance: int = 40) -> np.ndarray:
    """Replace a near-uniform background with a solid colour.

    Samples the background colour from the image border, builds a colour-distance
    mask, cleans it up, and fills matching pixels. Works best on plain, evenly-lit
    backgrounds; it is a simple offline method, not a segmentation model.
    """
    rgb = pixels[..., :3].astype(np.int16)
    h, w = rgb.shape[:2]
    border = np.concatenate([
        rgb[0, :], rgb[-1, :], rgb[:, 0], rgb[:, -1]
    ], axis=0)
    bg = np.median(border, axis=0)
    dist = np.sqrt(((rgb - bg) ** 2).sum(axis=-1))
    mask = (dist < tolerance).astype(np.uint8) * 255

    # Keep only background connected to the border (flood from edges),
    # so similar colours inside the subject are preserved.
    ff = mask.copy()
    fmask = np.zeros((h + 2, w + 2), np.uint8)
    for x in range(0, w, max(1, w // 50)):
        for y in (0, h - 1):
            if ff[y, x] == 255:
                cv2.floodFill(ff, fmask, (x, y), 128)
    for y in range(0, h, max(1, h // 50)):
        for x in (0, w - 1):
            if ff[y, x] == 255:
                cv2.floodFill(ff, fmask, (x, y), 128)
    bg_mask = (ff == 128).astype(np.uint8) * 255
    bg_mask = cv2.morphologyEx(bg_mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    bg_mask = cv2.GaussianBlur(bg_mask, (0, 0), 1.5)

    alpha = (bg_mask / 255.0)[..., None]
    out = pixels.copy()
    fill = np.array(list(new_color) + [255], dtype=np.float32)
    out = (out.astype(np.float32) * (1 - alpha) + fill * alpha).astype(np.uint8)
    out[..., 3] = 255
    return out


def _fit_photo(photo: np.ndarray, pw: int, ph: int) -> np.ndarray:
    """Resize/center-crop the photo to exactly (pw, ph)."""
    h, w = photo.shape[:2]
    scale = max(pw / w, ph / h)
    nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
    resized = cv2.resize(photo, (nw, nh), interpolation=cv2.INTER_AREA)
    x0 = (nw - pw) // 2
    y0 = (nh - ph) // 2
    return resized[y0:y0 + ph, x0:x0 + pw]


def build_print_sheet(photo: np.ndarray, photo_w_mm: float, photo_h_mm: float,
                      sheet: SheetSize, dpi: int = 300,
                      margin_mm: float = 5.0, gutter_mm: float = 2.0,
                      copies: int | None = None) -> np.ndarray:
    """Tile copies of a photo onto a print sheet. Returns RGBA at the given DPI."""
    sw = mm_to_px(sheet.width_mm, dpi)
    sh = mm_to_px(sheet.height_mm, dpi)
    pw = mm_to_px(photo_w_mm, dpi)
    ph = mm_to_px(photo_h_mm, dpi)
    if margin_mm < 0 or gutter_mm < 0:
        raise ValueError("Margins and gutters cannot be negative")
    margin = round(margin_mm / 25.4 * dpi)
    gutter = round(gutter_mm / 25.4 * dpi)
    if pw > sw - 2*margin or ph > sh - 2*margin:
        raise ValueError("The photo does not fit inside the sheet margins")

    canvas = np.full((sh, sw, 4), 255, dtype=np.uint8)
    tile = _fit_photo(photo, pw, ph)

    cols = max(1, (sw - 2 * margin + gutter) // (pw + gutter))
    rows = max(1, (sh - 2 * margin + gutter) // (ph + gutter))
    grid_w = cols * pw + (cols - 1) * gutter
    grid_h = rows * ph + (rows - 1) * gutter
    ox = (sw - grid_w) // 2
    oy = (sh - grid_h) // 2
    count = cols*rows if copies is None else int(copies)
    if count < 1 or count > cols*rows:
        raise ValueError(f"Choose between 1 and {cols*rows} copies")
    for r in range(rows):
        for c in range(cols):
            if r*cols+c >= count:
                continue
            x = ox + c * (pw + gutter)
            y = oy + r * (ph + gutter)
            canvas[y:y + ph, x:x + pw] = tile
            cv2.rectangle(canvas, (x, y), (x + pw - 1, y + ph - 1),
                          (210, 210, 210, 255), 1)
    return canvas


def sheet_capacity(photo_w_mm, photo_h_mm, sheet: SheetSize, dpi=300,
                   margin_mm=5.0, gutter_mm=2.0) -> tuple[int, int]:
    """Return (cols, rows) that fit — useful for tests and UI hints."""
    sw = mm_to_px(sheet.width_mm, dpi); sh = mm_to_px(sheet.height_mm, dpi)
    pw = mm_to_px(photo_w_mm, dpi); ph = mm_to_px(photo_h_mm, dpi)
    if margin_mm < 0 or gutter_mm < 0:
        raise ValueError("Margins and gutters cannot be negative")
    margin = round(margin_mm / 25.4 * dpi); gutter = round(gutter_mm / 25.4 * dpi)
    cols = max(0, (sw - 2 * margin + gutter) // (pw + gutter))
    rows = max(0, (sh - 2 * margin + gutter) // (ph + gutter))
    return int(cols), int(rows)


def export_pdf(pixels: np.ndarray, path: str | Path, dpi: int = 300) -> None:
    """Save an RGBA image as a single-page PDF at the given DPI."""
    img = Image.fromarray(pixels, mode="RGBA")
    bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
    flat = Image.alpha_composite(bg, img).convert("RGB")
    flat.save(Path(path), "PDF", resolution=float(dpi))
