"""Render editable object layers (TEXT, SHAPE) to RGBA pixel arrays.

Pure rendering from a spec dict; no Qt. Text uses a bundled/system TrueType font
when available, falling back to Pillow's built-in bitmap font so rendering always
works offline. Shapes are drawn with Pillow's ImageDraw.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

_FONT_DIR = Path(__file__).resolve().parent.parent / "resources" / "fonts"


@lru_cache(maxsize=32)
def _load_font(size: int, bold: bool) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    # Prefer a bundled font (offline-safe), then a common system font, then default.
    candidates = []
    if _FONT_DIR.exists():
        candidates += sorted(_FONT_DIR.glob("*.ttf"))
    candidates += [Path("C:/Windows/Fonts/segoeuib.ttf" if bold
                        else "C:/Windows/Fonts/segoeui.ttf"),
                   Path("C:/Windows/Fonts/arial.ttf"),
                   Path("DejaVuSans.ttf")]
    for path in candidates:
        try:
            return ImageFont.truetype(str(path), size)
        except Exception:
            continue
    return ImageFont.load_default()


def render_text(spec: dict) -> np.ndarray:
    w = max(1, int(spec.get("width", 1)))
    h = max(1, int(spec.get("height", 1)))
    text = str(spec.get("text", ""))
    color = tuple(spec.get("color", [20, 20, 20, 255]))
    align = spec.get("align", "center")
    font = _load_font(int(spec.get("font_size", 48)), bool(spec.get("bold", False)))

    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Multi-line aware placement.
    try:
        bbox = draw.multiline_textbbox((0, 0), text, font=font, align=align)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    except Exception:
        tw, th = draw.textlength(text, font=font), int(spec.get("font_size", 48))
    x = {"left": 0, "center": (w - tw) // 2, "right": w - tw}.get(align, (w - tw) // 2)
    y = max(0, (h - th) // 2)
    draw.multiline_text((x, y), text, fill=color, font=font, align=align)
    return np.asarray(img, dtype=np.uint8).copy()


def render_gradient(w: int, h: int, grad: dict) -> np.ndarray:
    """Linear gradient fill. grad = {angle_deg, stops:[[pos0..1, [r,g,b,a]], ...]}."""
    import math
    stops = grad.get("stops", [[0.0, [0, 0, 0, 255]], [1.0, [255, 255, 255, 255]]])
    stops = sorted(stops, key=lambda s: s[0])
    angle = math.radians(float(grad.get("angle", 0.0)))
    # Projection coordinate t in [0,1] along the gradient direction.
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    dx, dy = math.cos(angle), math.sin(angle)
    proj = xx * dx + yy * dy
    proj -= proj.min()
    denom = proj.max() if proj.max() > 0 else 1.0
    t = proj / denom
    pos = np.array([s[0] for s in stops], dtype=np.float32)
    cols = np.array([s[1] for s in stops], dtype=np.float32)
    out = np.empty((h, w, 4), dtype=np.float32)
    for ch in range(4):
        out[..., ch] = np.interp(t, pos, cols[:, ch])
    return np.clip(out, 0, 255).astype(np.uint8)


def render_shape(spec: dict) -> np.ndarray:
    w = max(1, int(spec.get("width", 1)))
    h = max(1, int(spec.get("height", 1)))
    if spec.get("gradient"):
        return render_gradient(w, h, spec["gradient"])
    shape = spec.get("shape", "rectangle")
    fill = tuple(spec["fill"]) if spec.get("fill") else None
    stroke = tuple(spec["stroke"]) if spec.get("stroke") else None
    sw = int(spec.get("stroke_width", 0))

    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    pad = max(0, sw // 2)
    box = (pad, pad, w - 1 - pad, h - 1 - pad)
    if shape in ("rectangle", "rect"):
        draw.rectangle(box, fill=fill, outline=stroke, width=sw)
    elif shape in ("ellipse", "circle"):
        draw.ellipse(box, fill=fill, outline=stroke, width=sw)
    elif shape in ("rounded", "rounded_rect"):
        r = int(min(w, h) * 0.18)
        draw.rounded_rectangle(box, radius=r, fill=fill, outline=stroke, width=sw)
    elif shape == "line":
        draw.line((0, h // 2, w, h // 2), fill=fill or stroke or (0, 0, 0, 255),
                  width=max(1, sw or 3))
    elif shape == "triangle":
        draw.polygon([(w // 2, pad), (pad, h - 1 - pad), (w - 1 - pad, h - 1 - pad)],
                     fill=fill, outline=stroke)
    else:
        draw.rectangle(box, fill=fill, outline=stroke, width=sw)
    return np.asarray(img, dtype=np.uint8).copy()


def render_object(kind, spec: dict) -> np.ndarray:
    """Dispatch by layer kind. `kind` is a LayerKind or its string value."""
    k = getattr(kind, "value", kind)
    if k == "text":
        return render_text(spec)
    if k == "shape":
        return render_shape(spec)
    raise ValueError(f"Cannot render object of kind {k!r}")
