"""Bundled, fully-offline, editable starter templates.

Each template is plain data that is built into a Document using the shared engine
(gradient/solid background + editable text + vector shapes). Every element stays
a real, editable layer — nothing is flattened — so users can customize freely and
export PNG/JPG. Content includes examples aimed at Somali small businesses,
schools, restaurants and community events. English/Latin text (Somali uses Latin
script); all strings are editable.

No internet, no external images, no third-party assets are required.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .document import Document, Layer


@dataclass
class Template:
    key: str
    name: str
    category: str
    width: int
    height: int
    layers: list = field(default_factory=list)
    dpi: int = 72


def _bg(color):               # solid background
    return {"bg": list(color)}


def _grad(stops, angle=90):   # gradient background
    return {"gradient": {"angle": angle, "stops": stops}}


def _shape(shape, x, y, w, h, fill=None, stroke=None, sw=0):
    return {"shape": shape, "x": x, "y": y, "w": w, "h": h,
            "fill": list(fill) if fill else None,
            "stroke": list(stroke) if stroke else None, "sw": sw}


def _text(text, x, y, w, h, size, color, align="center", bold=False):
    return {"text": text, "x": x, "y": y, "w": w, "h": h,
            "size": size, "color": list(color), "align": align, "bold": bold}


# Palette helpers (RGBA)
INK = (26, 29, 38, 255)
WHITE = (255, 255, 255, 255)
GOLD = (240, 190, 70, 255)
TEAL = (38, 166, 154, 255)
CORAL = (235, 90, 80, 255)
BLUE = (59, 102, 255, 255)
GREEN = (34, 160, 90, 255)


def build(template: Template) -> Document:
    """Construct an editable Document from a Template."""
    doc = Document.blank(template.width, template.height, name=template.name,
                         background=None, dpi=template.dpi)
    for spec in template.layers:
        if "bg" in spec:
            import numpy as np
            px = np.zeros((template.height, template.width, 4), dtype=np.uint8)
            px[:] = spec["bg"]
            doc.add_layer(Layer(pixels=px, name="Background"))
        elif "gradient" in spec:
            doc.add_layer(Document.make_gradient_layer(
                template.width, template.height, spec["gradient"]["stops"],
                angle=spec["gradient"]["angle"], name="Background"))
        elif "shape" in spec:
            layer = Document.make_shape_layer(
                spec["shape"], width=spec["w"], height=spec["h"],
                fill=tuple(spec["fill"]) if spec["fill"] else None,
                stroke=tuple(spec["stroke"]) if spec["stroke"] else None,
                stroke_width=spec["sw"])
            layer.offset = (spec["x"], spec["y"])
            doc.add_layer(layer)
        elif "art" in spec:
            from ..imaging.template_art import illustration
            pixels = illustration(spec["art"], spec["w"], spec["h"], spec["foreground"], spec["background"])
            layer = Layer(pixels=pixels, name=spec["name"])
            layer.offset = (spec["x"], spec["y"])
            doc.add_layer(layer)
        elif "text" in spec:
            layer = Document.make_text_layer(
                spec["text"], width=spec["w"], height=spec["h"],
                font_size=spec["size"], color=tuple(spec["color"]),
                align=spec["align"], bold=spec["bold"])
            layer.offset = (spec["x"], spec["y"])
            if "shadow_offset" in spec:
                layer.spec["shadow_offset"] = spec["shadow_offset"]
            doc.add_layer(layer)
        if "name" in spec and doc.layers:
            doc.layers[-1].name = spec["name"]
        if "rotation" in spec and doc.layers:
            doc.layers[-1].rotation = spec["rotation"]
    doc.active_layer_id = doc.layers[-1].id if doc.layers else None
    return doc


# ----------------------------------------------------------------------------
# Template catalogue (22 originals across 4 categories).
# ----------------------------------------------------------------------------
TEMPLATES: list[Template] = [
    Template("biz_phone", "Phone Shop", "Business", 1080, 1080, [
        _grad([[0, list(INK)], [1, list(BLUE)]], 45),
        _text("DUKAANKA TELEFOONNADA", 70, 100, 940, 180, 64, WHITE, bold=True),
        _shape("rounded", 390, 340, 300, 430, fill=WHITE),
        _shape("rounded", 420, 380, 240, 300, fill=TEAL),
        _text("Tayo sare · Qiimo fiican", 80, 820, 920, 90, 48, GOLD),
        _text("Wac: 061-XXXXXXX", 80, 950, 920, 60, 36, WHITE),
    ]),
    # ----- Business advertisements (Instagram 1080x1080) -----
    Template("biz_sale", "Big Sale Advert", "Business", 1080, 1080, [
        _grad([[0, list(BLUE)], [1, list(INK)]], 120),
        _shape("rounded", 90, 150, 900, 320, fill=WHITE),
        _text("IIBKA WEYN", 90, 180, 900, 140, 110, INK, bold=True),
        _text("BIG SALE", 90, 320, 900, 90, 64, BLUE, bold=True),
        _shape("rounded", 340, 560, 400, 150, fill=GOLD),
        _text("-50%", 340, 575, 400, 120, 96, INK, bold=True),
        _text("Dukaanka Magaalada  •  Call 061-XXXXXXX", 60, 940, 960, 60, 34, WHITE),
    ]),
    Template("biz_shop_open", "Shop Opening", "Business", 1080, 1080, [
        _bg(INK),
        _shape("rounded", 90, 120, 900, 260, fill=TEAL),
        _text("GRAND OPENING", 90, 170, 900, 120, 86, WHITE, bold=True),
        _text("Furitaanka Dukaanka Cusub", 90, 430, 900, 80, 48, GOLD),
        _text("Soo dhawoow! Qiimo jaban & tayo sare", 120, 560, 840, 120, 40, WHITE),
        _shape("rounded", 300, 780, 480, 130, fill=GOLD),
        _text("VISIT US TODAY", 300, 805, 480, 90, 52, INK, bold=True),
    ]),
    Template("biz_service", "Service Promo", "Business", 1080, 1080, [
        _grad([[0, list(TEAL)], [1, list(GREEN)]], 45),
        _shape("ellipse", 740, -120, 500, 500, fill=[255, 255, 255, 40]),
        _text("Adeeg Degdeg ah", 80, 200, 920, 120, 92, WHITE, bold=True),
        _text("Fast & Reliable Service", 80, 330, 920, 70, 46, WHITE),
        _shape("rounded", 80, 700, 920, 200, fill=WHITE),
        _text("Wac: 061-XXXXXXX", 80, 740, 920, 120, 64, INK, bold=True),
    ]),
    Template("biz_card", "Business Card", "Business", 1050, 600, [
        _grad([[0, list(INK)], [1, list(BLUE)]], 0),
        _text("MOHAMED IBRAHIM", 60, 150, 930, 90, 64, WHITE, "left", True),
        _text("Computer Engineer", 60, 250, 930, 60, 40, GOLD, "left"),
        _shape("line", 60, 340, 500, 6, fill=GOLD),
        _text("061-XXXXXXX  •  email@example.com", 60, 420, 930, 60, 34, WHITE, "left"),
    ]),
    Template("biz_discount_story", "Discount Story", "Business", 1080, 1920, [
        _grad([[0, list(CORAL)], [1, list(INK)]], 90),
        _text("OFARKA MAALINTA", 80, 300, 920, 120, 92, WHITE, bold=True),
        _shape("rounded", 240, 760, 600, 400, fill=WHITE),
        _text("30%", 240, 820, 600, 300, 220, CORAL, bold=True),
        _text("Ku dhaqaaq! Today only", 80, 1500, 920, 80, 48, WHITE),
    ]),

    # ----- Educational posters (A-ish portrait) -----
    Template("edu_school", "School Enrollment", "Education", 1080, 1350, [
        _grad([[0, list(BLUE)], [1, list(TEAL)]], 90),
        _shape("rounded", 80, 120, 920, 240, fill=WHITE),
        _text("ISKUULKA CUSUB", 80, 160, 920, 100, 78, BLUE, bold=True),
        _text("Enrollment Open 2026", 80, 420, 920, 70, 46, WHITE),
        _text("• Fasalada 1-12\n• Macalimiin khibrad leh\n• Qiimo macquul ah",
              140, 560, 820, 420, 44, WHITE, "left"),
        _shape("rounded", 300, 1150, 480, 120, fill=GOLD),
        _text("Is diiwaangeli", 300, 1175, 480, 80, 52, INK, bold=True),
    ]),
    Template("edu_study_tips", "Study Tips", "Education", 1080, 1350, [
        _bg(WHITE),
        _shape("rounded", 60, 60, 960, 180, fill=BLUE),
        _text("5 STUDY TIPS", 60, 100, 960, 100, 80, WHITE, bold=True),
        _text("1. Jadwal samee\n2. Nasasho qaado\n3. Su'aalo weydii\n"
              "4. Qoraal gacmeed\n5. Celcelis", 120, 320, 840, 760, 52, INK, "left"),
    ]),
    Template("edu_exam", "Exam Notice", "Education", 1080, 1350, [
        _grad([[0, list(INK)], [1, list(BLUE)]], 90),
        _text("IMTIXAANKA", 80, 220, 920, 120, 96, GOLD, bold=True),
        _text("Final Exams Schedule", 80, 360, 920, 70, 44, WHITE),
        _shape("rounded", 100, 520, 880, 560, fill=WHITE),
        _text("Taariikhda: __ / __ / 2026\nGoobta: Fasalka\nWaqtiga: 8:00 AM",
              150, 580, 780, 440, 48, INK, "left"),
    ]),
    Template("edu_library", "Library Event", "Education", 1080, 1350, [
        _grad([[0, list(GREEN)], [1, list(TEAL)]], 60),
        _text("AKHRIS MAALMEED", 70, 200, 940, 120, 84, WHITE, bold=True),
        _text("Reading Day at the Library", 70, 340, 940, 70, 42, WHITE),
        _shape("ellipse", 390, 560, 300, 300, fill=GOLD),
        _text("📚", 390, 600, 300, 220, 160, INK),
        _text("Ku soo biir! All students welcome", 70, 1150, 940, 80, 44, WHITE),
    ]),

    # ----- Restaurant promotions -----
    Template("rest_menu", "Restaurant Menu", "Restaurant", 1080, 1350, [
        _grad([[0, list(INK)], [1, [60, 30, 20, 255]]], 90),
        _text("MAKHAAYADDA", 60, 100, 960, 110, 84, GOLD, bold=True),
        _text("Today's Menu", 60, 230, 960, 60, 40, WHITE),
        _shape("line", 120, 330, 840, 4, fill=GOLD),
        _text("Bariis iyo Hilib ....... $5\nBaasto .............. $4\n"
              "Canjeero ............ $2\nShaah/Casiir ........ $1",
              120, 400, 840, 640, 48, WHITE, "left"),
    ]),
    Template("rest_special", "Daily Special", "Restaurant", 1080, 1080, [
        _grad([[0, list(CORAL)], [1, [120, 30, 30, 255]]], 45),
        _text("CUNTADA MAANTA", 70, 160, 940, 110, 82, WHITE, bold=True),
        _shape("rounded", 240, 400, 600, 320, fill=WHITE),
        _text("SPECIAL\n$6", 240, 440, 600, 260, 96, CORAL, bold=True),
        _text("Fadlan soo booqo  •  061-XXXXXXX", 60, 940, 960, 60, 36, WHITE),
    ]),
    Template("rest_coffee", "Coffee Promo", "Restaurant", 1080, 1080, [
        _bg([62, 39, 35, 255]),
        _shape("ellipse", 390, 240, 300, 300, fill=GOLD),
        _text("☕", 390, 290, 300, 220, 150, [62, 39, 35, 255]),
        _text("SHAAH & QAXWO", 90, 600, 900, 110, 82, WHITE, bold=True),
        _text("Fresh every morning", 90, 740, 900, 60, 42, GOLD),
    ]),
    Template("rest_delivery", "Delivery Offer", "Restaurant", 1080, 1080, [
        _grad([[0, list(GREEN)], [1, list(INK)]], 120),
        _text("GAARSIIN BILAASH AH", 70, 180, 940, 150, 76, WHITE, bold=True),
        _text("Free Delivery", 70, 360, 940, 70, 48, GOLD),
        _shape("rounded", 290, 620, 500, 180, fill=GOLD),
        _text("ORDER NOW", 290, 660, 500, 100, 64, INK, bold=True),
    ]),
    Template("rest_iftar", "Iftar Special", "Restaurant", 1080, 1350, [
        _grad([[0, [40, 20, 60, 255]], [1, list(INK)]], 90),
        _text("IFTAAR", 80, 240, 920, 160, 130, GOLD, bold=True),
        _shape("ellipse", 440, 480, 200, 200, fill=[255, 255, 255, 40]),
        _text("Special Ramadan Menu", 80, 760, 920, 70, 46, WHITE),
        _text("Open at Maghrib  •  061-XXXXXXX", 80, 1150, 920, 60, 38, WHITE),
    ]),

    # ----- Events / community -----
    Template("evt_wedding", "Wedding Invite", "Events", 1080, 1350, [
        _grad([[0, [245, 240, 235, 255]], [1, [230, 215, 200, 255]]], 90),
        _text("CASUUMAAD", 90, 220, 900, 120, 92, INK, bold=True),
        _text("You are invited", 90, 360, 900, 60, 40, [120, 90, 70, 255]),
        _shape("line", 290, 470, 500, 3, fill=GOLD),
        _text("Aroos  •  Wedding", 90, 560, 900, 100, 64, INK),
        _text("Taariikh: __ / __ / 2026\nGoobta: ____", 90, 760, 900, 300, 46, INK),
    ]),
    Template("evt_conference", "Conference", "Events", 1080, 1350, [
        _grad([[0, list(BLUE)], [1, list(INK)]], 60),
        _text("SHIRWEYNE", 80, 180, 920, 120, 96, WHITE, bold=True),
        _text("Community Conference 2026", 80, 320, 920, 70, 44, GOLD),
        _shape("rounded", 100, 520, 880, 520, fill=[255, 255, 255, 25]),
        _text("Topic: Horumarinta Dhallinyarada\nDate: __ / __\nVenue: ____",
              150, 580, 780, 400, 46, WHITE, "left"),
    ]),
    Template("evt_sports", "Sports Day", "Events", 1080, 1080, [
        _grad([[0, list(GREEN)], [1, list(TEAL)]], 45),
        _text("CIYAARAHA", 70, 160, 940, 130, 100, WHITE, bold=True),
        _text("Community Sports Day", 70, 320, 940, 70, 46, GOLD),
        _shape("ellipse", 420, 480, 240, 240, fill=WHITE),
        _text("⚽", 420, 520, 240, 180, 130, GREEN),
        _text("Ku soo biir! Register now", 70, 900, 940, 70, 44, WHITE),
    ]),
    Template("evt_charity", "Charity Drive", "Events", 1080, 1350, [
        _grad([[0, list(CORAL)], [1, list(INK)]], 90),
        _text("SADAQO", 80, 240, 920, 140, 120, WHITE, bold=True),
        _text("Charity & Donation Drive", 80, 400, 920, 70, 44, GOLD),
        _text("Caawi qoysaska baahan\nHelp families in need",
              120, 640, 840, 240, 50, WHITE),
        _shape("rounded", 300, 1120, 480, 130, fill=GOLD),
        _text("Donate", 300, 1150, 480, 80, 56, INK, bold=True),
    ]),
    Template("evt_eid", "Eid Greeting", "Events", 1080, 1080, [
        _grad([[0, [30, 80, 70, 255]], [1, list(INK)]], 120),
        _shape("ellipse", 760, 120, 200, 200, fill=GOLD),
        _text("EID MUBARAK", 80, 420, 920, 150, 120, GOLD, bold=True),
        _text("Ciid wanaagsan", 80, 620, 920, 80, 56, WHITE),
    ]),
    Template("evt_youth", "Youth Meetup", "Events", 1080, 1080, [
        _grad([[0, list(BLUE)], [1, list(TEAL)]], 30),
        _text("DHALLINYARO", 70, 200, 940, 130, 96, WHITE, bold=True),
        _text("Youth Meetup & Skills", 70, 350, 940, 70, 46, GOLD),
        _shape("rounded", 140, 560, 800, 320, fill=[255, 255, 255, 20]),
        _text("Barasho • Networking • Fun", 140, 680, 800, 80, 46, WHITE),
    ]),
    Template("evt_announcement", "Announcement", "Events", 1080, 1080, [
        _bg(INK),
        _shape("rounded", 80, 360, 920, 360, fill=GOLD),
        _text("OGEYSIIS", 80, 180, 920, 120, 92, GOLD, bold=True),
        _text("Your announcement text here\nWrite details...",
              120, 420, 840, 260, 50, INK),
    ]),
]


EXISTING_KEYS = tuple(t.key for t in TEMPLATES)
from .template_collection import new_templates
NEW_TEMPLATES = new_templates(Template)
TEMPLATES.extend(NEW_TEMPLATES)


def by_category() -> dict[str, list[Template]]:
    out: dict[str, list[Template]] = {}
    for t in TEMPLATES:
        out.setdefault(t.category, []).append(t)
    return out


def get(key: str) -> Template:
    for t in TEMPLATES:
        if t.key == key:
            return t
    raise KeyError(key)
