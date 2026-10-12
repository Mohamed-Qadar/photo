"""Export-only attribution; never changes document layers or source pixels."""
import numpy as np
from PIL import Image, ImageDraw
from .render import _load_font

WATERMARK_TEXT = "Developed by Eng. Mohamed Ibrahim Abdi"


def apply_watermark(pixels):
    image = Image.fromarray(pixels, "RGBA").copy()
    width, height = image.size
    overlay = Image.new("RGBA", image.size)
    draw = ImageDraw.Draw(overlay)
    margin = max(1, round(min(width, height) * .018))
    size = max(1, min(round(min(width, height) * .022), 96))
    # Fit even narrow and tiny exports. A subtle dark plate stays legible on any color.
    while True:
        font = _load_font(size, False)
        box = draw.textbbox((0, 0), WATERMARK_TEXT, font=font)
        tw, th = box[2]-box[0], box[3]-box[1]
        if tw + margin*4 <= width or size == 1:
            break
        size -= 1
    padding = max(1, round(size * .4))
    x = max(0, (width-tw)//2)
    y = max(0, height-margin-padding-th)
    draw.rounded_rectangle((max(0, x-padding), max(0, y-padding),
                            min(width-1, x+tw+padding), min(height-1, y+th+padding)),
                           radius=padding, fill=(20, 24, 32, 170))
    draw.text((x-box[0], y-box[1]), WATERMARK_TEXT, font=font, fill=(255, 255, 255, 245))
    return np.asarray(Image.alpha_composite(image, overlay), dtype=np.uint8).copy()
