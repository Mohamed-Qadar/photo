"""Generate PhotoStudio's original app icon (no third-party assets).

Produces resources/icon.ico (multi-size) and resources/icon.png.
A rounded-square badge with an overlapping aperture + canvas motif in the
app's accent blue. Run:  python tool/make_icon.py
"""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent.parent / "photostudio" / "resources"
ACCENT = (91, 140, 255, 255)
ACCENT_DK = (51, 102, 255, 255)
BG = (27, 29, 35, 255)
WHITE = (240, 243, 250, 255)


def rounded(draw, box, radius, fill):
    draw.rounded_rectangle(box, radius=radius, fill=fill)


def render(size: int) -> Image.Image:
    s = size
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pad = int(s * 0.06)
    # Badge background with gradient-ish two-tone.
    rounded(d, (pad, pad, s - pad, s - pad), int(s * 0.22), BG)
    rounded(d, (pad, pad, s - pad, int(s * 0.55)), int(s * 0.22), (35, 38, 46, 255))

    cx, cy = s / 2, s * 0.46
    r = s * 0.24
    # Aperture: six blades as a ring of lines.
    for i in range(6):
        a = math.radians(60 * i + 15)
        x1 = cx + r * math.cos(a)
        y1 = cy + r * math.sin(a)
        a2 = a + math.radians(55)
        x2 = cx + r * math.cos(a2)
        y2 = cy + r * math.sin(a2)
        d.line([(x1, y1), (x2, y2)], fill=ACCENT, width=max(2, int(s * 0.03)))
    d.ellipse((cx - r * 0.45, cy - r * 0.45, cx + r * 0.45, cy + r * 0.45),
              fill=ACCENT_DK)

    # "Canvas/design" base bar.
    by = int(s * 0.70)
    rounded(d, (int(s * 0.28), by, int(s * 0.72), by + int(s * 0.07)),
            int(s * 0.035), WHITE)
    rounded(d, (int(s * 0.28), by + int(s * 0.10), int(s * 0.60),
                by + int(s * 0.17)), int(s * 0.035), ACCENT)
    return img


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    sizes = [16, 24, 32, 48, 64, 128, 256]
    imgs = [render(sz) for sz in sizes]
    base = render(256)
    base.save(OUT / "icon.png")
    base.save(OUT / "icon.ico", format="ICO",
              sizes=[(sz, sz) for sz in sizes])
    print(f"Wrote {OUT/'icon.ico'} and {OUT/'icon.png'}")


if __name__ == "__main__":
    main()
