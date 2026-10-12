"""Original geometric illustrations, generated locally; replaceable image layers.

No stock photography, logos, downloadable fonts or external assets are used.
"""
import numpy as np
from PIL import Image, ImageDraw


def illustration(kind, width, height, foreground, background):
    # Draw in a 400-unit square, then fit within the image slot without distortion.
    image = Image.new("RGBA", (400, 400), tuple(background))
    d = ImageDraw.Draw(image)
    c = tuple(foreground)
    light = (255, 255, 255, 230)
    dark = (20, 30, 48, 255)
    if kind in ("portrait", "fashion", "beauty", "graduate"):
        d.ellipse((105, 45, 295, 235), fill=c)
        d.rounded_rectangle((50, 245, 350, 470), radius=90, fill=c)
        d.pieslice((100, 30, 300, 230), 180, 360, fill=dark)
        if kind == "graduate":
            d.polygon([(55, 65), (200, 10), (345, 65), (200, 125)], fill=dark)
            d.line((330, 70, 330, 180), fill=light, width=8)
        if kind == "beauty":
            d.arc((110, 70, 290, 240), 20, 160, fill=light, width=6)
    elif kind == "phone":
        d.rounded_rectangle((110, 20, 290, 380), radius=28, fill=dark)
        d.rounded_rectangle((125, 42, 275, 352), radius=18, fill=c)
        d.ellipse((225, 62, 248, 85), fill=light)
        d.line((167, 366, 233, 366), fill=light, width=5)
        d.polygon([(125, 230), (275, 100), (275, 250), (125, 330)], fill=(255, 255, 255, 60))
    elif kind == "food":
        d.ellipse((35, 35, 365, 365), fill=light)
        d.ellipse((65, 65, 335, 335), fill=c)
        for box in [(100, 100, 225, 160), (140, 190, 280, 250), (105, 270, 245, 295)]:
            d.rounded_rectangle(box, radius=20, fill=dark)
        for x, y in [(120, 190), (260, 120), (280, 270)]:
            d.ellipse((x-16, y-16, x+16, y+16), fill=(91, 152, 92, 255))
    elif kind == "house":
        d.polygon([(25, 175), (200, 35), (375, 175)], fill=c)
        d.rectangle((65, 175, 335, 345), fill=light)
        d.rectangle((170, 245, 225, 345), fill=dark)
        for x in (90, 255):
            d.rectangle((x, 210, x+45, 260), fill=c)
        d.rectangle((45, 345, 355, 365), fill=c)
    elif kind == "router":
        d.rounded_rectangle((65, 250, 335, 335), radius=20, fill=c)
        for x in (105, 295): d.line((x, 255, x, 140), fill=light, width=12)
        for r in (70, 120, 170): d.arc((200-r, 175-r, 200+r, 175+r), 215, 325, fill=light, width=12)
        for x in (100, 135, 170): d.ellipse((x, 280, x+12, 292), fill=light)
    elif kind == "basket":
        d.polygon([(70, 150), (330, 150), (290, 335), (110, 335)], fill=c)
        d.line((120, 160, 200, 55, 280, 160), fill=light, width=16)
        for x in (140, 190, 240): d.line((x, 185, x, 300), fill=light, width=8)
    elif kind in ("moon", "lantern"):
        d.ellipse((70, 45, 330, 305), fill=c)
        d.ellipse((140, 5, 360, 225), fill=tuple(background))
        d.polygon([(300, 245), (311, 278), (345, 278), (318, 298), (328, 331), (300, 310), (272, 331), (282, 298), (255, 278), (289, 278)], fill=light)
        if kind == "lantern":
            d.line((65, 0, 65, 180), fill=c, width=4)
            d.rounded_rectangle((35, 180, 95, 290), radius=14, fill=c)
    elif kind in ("ring", "bouquet"):
        if kind == "ring":
            d.ellipse((55, 125, 245, 315), outline=c, width=15)
            d.ellipse((160, 80, 350, 270), outline=c, width=15)
            d.polygon([(217, 70), (250, 35), (283, 70), (250, 105)], fill=light)
        else:
            for x, y in [(120, 135), (200, 85), (285, 155)]:
                d.line((x, y, 210, 350), fill=c, width=8)
                for dx, dy in [(-25, 0), (25, 0), (0, -25), (0, 25)]:
                    d.ellipse((x+dx-25, y+dy-25, x+dx+25, y+dy+25), fill=light)
                d.ellipse((x-14, y-14, x+14, y+14), fill=c)
    elif kind == "cake":
        d.rounded_rectangle((60, 220, 340, 335), radius=15, fill=c)
        d.rounded_rectangle((90, 150, 310, 235), radius=15, fill=light)
        for x in (140, 200, 260):
            d.line((x, 155, x, 100), fill=c, width=8)
            d.ellipse((x-7, 70, x+7, 95), fill=(246, 182, 80, 255))
    elif kind in ("book", "course"):
        d.polygon([(55, 60), (185, 80), (200, 340), (55, 300)], fill=light)
        d.polygon([(200, 80), (345, 50), (345, 300), (200, 340)], fill=c)
        d.line((200, 80, 200, 340), fill=dark, width=10)
        for y in (120, 170, 220): d.line((80, y, 160, y+15), fill=c, width=8)
    elif kind in ("badge", "crest"):
        d.polygon([(80, 40), (320, 40), (335, 240), (200, 365), (65, 240)], fill=c)
        d.polygon([(105, 70), (295, 70), (305, 220), (200, 325), (95, 220)], outline=light, width=8)
        d.ellipse((145, 125, 255, 235), fill=light)
        d.polygon([(200, 140), (230, 165), (220, 205), (180, 205), (170, 165)], fill=dark)
    elif kind in ("microphone", "podcast"):
        d.rounded_rectangle((145, 45, 255, 230), radius=50, fill=c)
        d.arc((105, 115, 295, 300), 0, 180, fill=light, width=12)
        d.line((200, 285, 200, 345), fill=light, width=12)
        d.line((130, 345, 270, 345), fill=light, width=12)
        for y in (85, 115, 145): d.line((170, y, 230, y), fill=light, width=5)
    elif kind == "play":
        d.rounded_rectangle((35, 80, 365, 320), radius=55, fill=c)
        d.polygon([(165, 130), (165, 270), (280, 200)], fill=light)
    elif kind == "ball":
        d.ellipse((45, 45, 355, 355), fill=light)
        d.polygon([(200, 120), (270, 170), (244, 253), (156, 253), (130, 170)], fill=dark)
        for x, y in [(100, 70), (300, 75), (345, 250), (205, 345), (60, 260)]:
            d.ellipse((x-35, y-35, x+35, y+35), fill=c)
    else:  # Original logo/photo motif for civic and abstract designs.
        d.ellipse((45, 45, 355, 355), outline=c, width=16)
        for x, y, r in [(200, 105, 28), (120, 185, 22), (280, 185, 22)]:
            d.ellipse((x-r, y-r, x+r, y+r), fill=light)
            d.rounded_rectangle((x-r-12, y+r+12, x+r+12, y+r+100), radius=20, fill=c)
    # Letterbox to preserve the artwork's proportions in any replaceable slot.
    image.thumbnail((width, height), Image.Resampling.LANCZOS)
    result = Image.new("RGBA", (width, height), tuple(background))
    result.alpha_composite(image, ((width-image.width)//2, (height-image.height)//2))
    return np.asarray(result, dtype=np.uint8).copy()
