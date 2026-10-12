"""Home landing screen: hero + workspace tiles.

Tiles emit `workspace_selected(key)`. Tiles that are implemented are enabled;
planned ones carry a clear "Soon" badge and are disabled (no fake buttons).
Backgrounds are explicitly transparent so no dark rectangles appear behind text.
"""
from __future__ import annotations
from .i18n import tr, source_text

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QFrame, QGridLayout, QHBoxLayout, QLabel,
                               QScrollArea, QVBoxLayout, QWidget, QListWidget, QListWidgetItem)

from .. import __version__

# key, title, subtitle, implemented?
TILES = [
    ("new_design", "New Design", "Blank canvas at any size.", True),
    ("photo_editor", "Photo Editor", "Open a photo to crop, adjust & export.", True),
    ("social", "Social Media Designer", "Posts, stories, thumbnails with text & shapes.", True),
    ("graphic", "Graphic Design", "Posters, flyers, cards, banners, logos.", True),
    ("custom", "Custom Canvas", "Pick exact width, height and DPI.", True),
    ("open_project", "Open Project", "Resume a saved .pstudio project.", True),
    ("templates", "Templates", "62 editable offline designs across 11 categories.", True),
    ("beauty", "Beauty Studio", "Skin smoothing, spot removal, background blur.", True),
    ("passport", "Passport & ID Photo", "Sizes, background swap, print sheets, PDF.", True),
]


class Tile(QFrame):
    clicked = Signal(str)

    def __init__(self, key: str, title: str, subtitle: str, enabled: bool):
        super().__init__()
        self.key = key
        self._enabled = enabled
        self.setObjectName("tile")
        self.setMinimumHeight(118)
        self.setCursor(Qt.CursorShape.PointingHandCursor if enabled
                       else Qt.CursorShape.ArrowCursor)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 16, 18, 16)
        lay.setSpacing(6)

        row = QHBoxLayout()
        t = QLabel(tr(title))
        t.setObjectName("tileTitle")
        t.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        row.addWidget(t)
        row.addStretch(1)
        if not enabled:
            badge = QLabel(tr("Soon"))
            badge.setObjectName("badge")
            row.addWidget(badge)
        lay.addLayout(row)

        s = QLabel(tr(subtitle))
        s.setObjectName("tileSub")
        s.setWordWrap(True)
        s.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        lay.addWidget(s)
        lay.addStretch(1)
        self.setProperty("enabled_tile", enabled)

    def mouseReleaseEvent(self, event):
        if self._enabled and event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.key)
        super().mouseReleaseEvent(event)


class HomeScreen(QWidget):
    workspace_selected = Signal(str)
    recent_selected = Signal(str)

    def __init__(self):
        super().__init__()
        self.setObjectName("home")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        outer.addWidget(scroll)

        content = QWidget()
        content.setObjectName("homeContent")
        scroll.setWidget(content)
        root = QVBoxLayout(content)
        root.setContentsMargins(56, 44, 56, 44)
        root.setSpacing(8)

        # Hero
        hero = QLabel(tr("PhotoStudio"))
        hero.setObjectName("hero")
        tagline = QLabel(tr("A complete offline creative studio — design, edit and export, "
                         "no account and no internet required."))
        tagline.setObjectName("heroSub")
        tagline.setWordWrap(True)
        root.addWidget(hero)
        root.addWidget(tagline)
        root.addSpacing(28)

        start = QLabel(tr("Start creating"))
        start.setObjectName("sectionTitle")
        root.addWidget(start)
        root.addSpacing(8)

        grid = QGridLayout()
        grid.setSpacing(16)
        root.addLayout(grid)
        for i, (key, title, sub, enabled) in enumerate(TILES):
            tile = Tile(key, title, sub, enabled)
            if enabled:
                tile.clicked.connect(self.workspace_selected.emit)
            grid.addWidget(tile, i // 3, i % 3)

        root.addSpacing(20)
        root.addWidget(QLabel(tr("Recent Projects")))
        self.recent = QListWidget()
        self.recent.setMaximumHeight(140)
        self.recent.itemDoubleClicked.connect(
            lambda item: self.recent_selected.emit(item.data(Qt.ItemDataRole.UserRole))
            if item.data(Qt.ItemDataRole.UserRole) else None)
        root.addWidget(self.recent)
        root.addStretch(1)
        foot = QLabel(tr(f"Version {__version__} · Developed by Eng. Mohamed Ibrahim Abdi — "
                      "Computer Engineer (NLP & Computer Vision)"))
        foot.setObjectName("homeFoot")
        root.addWidget(foot)

    def set_recent(self, paths):
        from pathlib import Path
        self.recent.clear()
        for path in paths:
            if Path(path).exists():
                item = QListWidgetItem(f"{Path(path).name} — {path}")
                item.setData(Qt.ItemDataRole.UserRole, path)
                self.recent.addItem(item)
        if not self.recent.count():
            self.recent.addItem(tr("No recent projects"))
