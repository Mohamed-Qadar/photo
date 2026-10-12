"""Canvas presets for social-media and graphic-design workspaces (pixels @ dpi)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CanvasPreset:
    key: str
    label: str
    width: int
    height: int
    dpi: int = 72
    category: str = "General"


SOCIAL_PRESETS = [
    CanvasPreset("ig_post", "Instagram Post (1080×1080)", 1080, 1080, 72, "Instagram"),
    CanvasPreset("ig_portrait", "Instagram Portrait (1080×1350)", 1080, 1350, 72, "Instagram"),
    CanvasPreset("ig_story", "Instagram Story (1080×1920)", 1080, 1920, 72, "Instagram"),
    CanvasPreset("fb_post", "Facebook Post (1200×630)", 1200, 630, 72, "Facebook"),
    CanvasPreset("fb_cover", "Facebook Cover (1640×624)", 1640, 624, 72, "Facebook"),
    CanvasPreset("yt_thumb", "YouTube Thumbnail (1280×720)", 1280, 720, 72, "YouTube"),
    CanvasPreset("tiktok", "TikTok Cover (1080×1920)", 1080, 1920, 72, "TikTok"),
    CanvasPreset("wa_status", "WhatsApp Status (1080×1920)", 1080, 1920, 72, "WhatsApp"),
]

GRAPHIC_PRESETS = [
    CanvasPreset("poster_a3", "Poster A3 (3508×4961 @300)", 3508, 4961, 300, "Poster"),
    CanvasPreset("poster_a4", "Poster A4 (2480×3508 @300)", 2480, 3508, 300, "Poster"),
    CanvasPreset("flyer", "Flyer A5 (1748×2480 @300)", 1748, 2480, 300, "Flyer"),
    CanvasPreset("business_card", "Business Card (1050×600 @300)", 1050, 600, 300, "Card"),
    CanvasPreset("banner", "Web Banner (1500×500)", 1500, 500, 72, "Banner"),
    CanvasPreset("logo", "Logo (1000×1000)", 1000, 1000, 72, "Logo"),
]


def all_presets():
    return SOCIAL_PRESETS + GRAPHIC_PRESETS
