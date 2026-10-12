"""Dark (default) and light theme tokens + Qt stylesheet.

Original palette — no third-party branded colors or assets.
"""
from __future__ import annotations

DARK = {
    "bg": "#1b1d23",
    "bg_elevated": "#23262e",
    "panel": "#20232a",
    "border": "#31353f",
    "text": "#e6e8ee",
    "text_muted": "#9aa0ad",
    "accent": "#5b8cff",
    "accent_hover": "#6f9bff",
    "canvas_bg": "#15171c",
    "disabled": "#5a5f6b",
}

LIGHT = {
    "bg": "#f4f5f7",
    "bg_elevated": "#ffffff",
    "panel": "#ececf0",
    "border": "#d6d8de",
    "text": "#1b1d23",
    "text_muted": "#6b7080",
    "accent": "#3366ff",
    "accent_hover": "#4a78ff",
    "canvas_bg": "#dcdee3",
    "disabled": "#b4b8c0",
}


def stylesheet(tokens: dict[str, str]) -> str:
    t = tokens
    return f"""
    QMainWindow, QWidget {{
        background: {t['bg']};
        color: {t['text']};
        font-family: 'Segoe UI', 'Inter', sans-serif;
        font-size: 13px;
    }}
    QMenuBar {{ background: {t['bg_elevated']}; border-bottom: 1px solid {t['border']}; }}
    QMenuBar::item:selected {{ background: {t['accent']}; color: white; }}
    QMenu {{ background: {t['bg_elevated']}; border: 1px solid {t['border']}; }}
    QMenu::item:selected {{ background: {t['accent']}; color: white; }}
    QToolBar {{ background: {t['bg_elevated']}; border: none; spacing: 4px; padding: 4px; }}
    QDockWidget {{ titlebar-close-icon: none; color: {t['text_muted']}; }}
    QDockWidget::title {{ background: {t['panel']}; padding: 6px 10px; }}
    QPushButton {{
        background: {t['bg_elevated']}; border: 1px solid {t['border']};
        border-radius: 6px; padding: 7px 14px; color: {t['text']};
    }}
    QPushButton:hover {{ border-color: {t['accent']}; }}
    QPushButton:disabled {{ color: {t['disabled']}; border-color: {t['border']}; }}
    QPushButton#primary {{ background: {t['accent']}; border: none; color: white; font-weight: 600; }}
    QPushButton#primary:hover {{ background: {t['accent_hover']}; }}
    QLabel#title {{ font-size: 22px; font-weight: 700; }}
    QLabel#subtitle {{ color: {t['text_muted']}; }}
    QLabel#muted {{ color: {t['text_muted']}; }}
    QSlider::groove:horizontal {{ height: 4px; background: {t['border']}; border-radius: 2px; }}
    QSlider::handle:horizontal {{
        background: {t['accent']}; width: 14px; height: 14px;
        margin: -6px 0; border-radius: 7px;
    }}
    QListWidget, QTreeWidget {{
        background: {t['panel']}; border: 1px solid {t['border']}; border-radius: 6px;
    }}
    QListWidget::item:selected {{ background: {t['accent']}; color: white; }}
    QFrame#card {{
        background: {t['bg_elevated']}; border: 1px solid {t['border']}; border-radius: 10px;
    }}
    QFrame#card:hover {{ border-color: {t['accent']}; }}
    QStatusBar {{ background: {t['bg_elevated']}; color: {t['text_muted']}; }}

    /* ---- Home screen ---- */
    QWidget#homeContent {{ background: {t['bg']}; }}
    QScrollArea {{ background: {t['bg']}; border: none; }}
    QLabel {{ background: transparent; }}
    QLabel#hero {{ font-size: 40px; font-weight: 800; letter-spacing: 0.5px; }}
    QLabel#heroSub {{ font-size: 15px; color: {t['text_muted']}; }}
    QLabel#sectionTitle {{ font-size: 15px; font-weight: 700; color: {t['text_muted']}; }}
    QLabel#homeFoot {{ color: {t['text_muted']}; font-size: 12px; }}
    QFrame#tile {{
        background: {t['bg_elevated']};
        border: 1px solid {t['border']};
        border-radius: 14px;
    }}
    QFrame#tile[enabled_tile="true"]:hover {{ border: 1px solid {t['accent']}; }}
    QLabel#tileTitle {{ font-size: 17px; font-weight: 600; }}
    QLabel#tileSub {{ color: {t['text_muted']}; font-size: 13px; }}
    QLabel#badge {{
        background: {t['border']}; color: {t['text_muted']};
        border-radius: 8px; padding: 2px 8px; font-size: 11px; font-weight: 600;
    }}
    """
