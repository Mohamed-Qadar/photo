"""Compositing pipeline: Document -> flattened RGBA ndarray.

Applies each layer's non-destructive adjustments, then alpha-blends layers
bottom to top honouring opacity and blend mode. No Qt imports.
"""
from __future__ import annotations

import numpy as np
import copy
import math

from .document import BlendMode, Document, Layer
from ..imaging.adjustments import apply_adjustments


def _blend(base_rgb: np.ndarray, top_rgb: np.ndarray, mode: BlendMode) -> np.ndarray:
    if mode == BlendMode.MULTIPLY:
        return base_rgb * top_rgb / 255.0
    if mode == BlendMode.SCREEN:
        return 255.0 - (255.0 - base_rgb) * (255.0 - top_rgb) / 255.0
    return top_rgb  # NORMAL


def _composite_layer(canvas: np.ndarray, layer: Layer, use_adjustments: bool = True) -> None:
    """Blend one layer into `canvas` (float32 RGBA, in place)."""
    base = layer.render()
    src = (apply_adjustments(base, layer.adjustments) if use_adjustments
           else base).astype(np.float32)
    ox, oy = layer.offset
    ch, cw = canvas.shape[:2]
    lh, lw = src.shape[:2]

    # Intersect layer rect with canvas rect.
    x0, y0 = max(0, ox), max(0, oy)
    x1, y1 = min(cw, ox + lw), min(ch, oy + lh)
    if x1 <= x0 or y1 <= y0:
        return
    sx0, sy0 = x0 - ox, y0 - oy
    src_rgb = _src = src[sy0:sy0 + (y1 - y0), sx0:sx0 + (x1 - x0)]
    dst = canvas[y0:y1, x0:x1]

    top_rgb = src_rgb[..., :3]
    top_a = (src_rgb[..., 3:4] / 255.0) * float(layer.opacity)
    base_rgb = dst[..., :3]
    base_a = dst[..., 3:4] / 255.0

    blended_rgb = _blend(base_rgb, top_rgb, layer.blend)
    out_a = top_a + base_a * (1.0 - top_a)
    safe_a = np.where(out_a > 1e-6, out_a, 1.0)
    out_rgb = (blended_rgb * top_a + base_rgb * base_a * (1.0 - top_a)) / safe_a

    dst[..., :3] = out_rgb
    dst[..., 3:4] = out_a * 255.0


def composite(document: Document, use_adjustments: bool = True) -> np.ndarray:
    """Return the flattened document as H x W x 4 uint8 RGBA.

    use_adjustments=False renders the "before" image (raw pixels, no tone edits)
    for before/after comparison.
    """
    canvas = np.zeros((document.height, document.width, 4), dtype=np.float32)
    for layer in document.layers:
        if not layer.visible or layer.opacity <= 0.0:
            continue
        _composite_layer(canvas, layer, use_adjustments=use_adjustments)
    return np.clip(canvas, 0, 255).astype(np.uint8)


def preview_document(document: Document, max_side: int = 1600) -> Document:
    """Bounded preview model. Source arrays/specs remain unchanged."""
    from ..imaging.transforms import resize
    ratio = min(1.0, max_side / max(document.width, document.height))
    if ratio == 1:
        return document
    doc = copy.copy(document)
    doc.width, doc.height = max(1, round(doc.width*ratio)), max(1, round(doc.height*ratio))
    doc.layers = []
    for layer in document.layers:
        item = copy.copy(layer)
        item.offset = (round(layer.offset[0]*ratio), round(layer.offset[1]*ratio))
        # Render at preview resolution before applying editable scale and rotation.
        w, h = max(1, round(layer.width*ratio)), max(1, round(layer.height*ratio))
        if layer.pixels is not None:
            item.pixels = resize(layer.pixels, w, h)
        else:
            item.spec = copy.deepcopy(layer.spec)
            item.spec.update(width=w, height=h)
            for key in ("font_size", "stroke_width", "outline_width", "shadow_offset"):
                if key in item.spec:
                    item.spec[key] = max(1 if key == "font_size" else 0, round(item.spec[key]*ratio))
        doc.layers.append(item)
    return doc


def composite_preview(document, use_adjustments=True, max_side=1600):
    return composite(preview_document(document, max_side), use_adjustments=use_adjustments)
