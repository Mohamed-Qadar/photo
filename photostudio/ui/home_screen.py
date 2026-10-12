"""Home landing screen with action cards."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QFrame, QGridLayout, QLabel, QVBoxLayout, QWidget)


class _Card(QFrame):
    clicked = Signal()

    def __init__(self, title: str, subtitle: str, enabled: bool = True):
        super().__init__()
        self.setObjectName("card")
        self.setCursor(Qt.CursorShape.PointingHandCursor if enabled
                       else Qt.CursorShape.ForbiddenCursor)
        self._enabled = enabled
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        t = QLabel(title)
        t.setStyleSheet("font-size:16px; font-weight:600;")
        s = QLabel(subtitle)
        s.setObjectName("muted")
        s.setWordWrap(True)
        layout.addWidget(t)
        layout.addWidget(s)
        layout.addStretch(1)
        if not enabled:
            self.setStyleSheet("QFrame#card { opacity: 0.5; }")

    def mouseReleaseEvent(self, event):
        if self._enabled and event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mouseReleaseEvent(event)


class HomeScreen(QWidget):
    new_project = Signal()
    edit_photo = Signal()
    open_project = Signal()

    def __init__(self):
        super().__init__()
        root = QVBoxLayout(self)
        root.setContentsMargins(48, 40, 48, 40)
        root.setSpacing(6)

        title = QLabel("PhotoStudio")
        title.setObjectName("title")
        subtitle = QLabel("Offline photo & design studio — pick a starting point.")
        subtitle.setObjectName("subtitle")
        root.addWidget(title)
        root.addWidget(subtitle)
        root.addSpacing(24)

        grid = QGridLayout()
        grid.setSpacing(16)
        root.addLayout(grid)

        cards = [
            ("New Project", "Start a blank canvas.", True, self.new_project),
            ("Edit Photo", "Open an image to crop, adjust and export.", True, self.edit_photo),
            ("Open Project", "Resume a saved .pstudio project.", True, self.open_project),
            ("Beauty Studio", "Portrait retouch — coming in Phase 4.", False, None),
            ("Social Media", "Post & story canvases — coming in Phase 3.", False, None),
            ("Passport Photo", "Biometric & ID photos — coming in Phase 5.", False, None),
        ]
        for i, (t, s, enabled, signal) in enumerate(cards):
            card = _Card(t, s, enabled)
            if enabled and signal is not None:
                card.clicked.connect(signal.emit)
            grid.addWidget(card, i // 3, i % 3)

        root.addStretch(1)
        note = QLabel("Disabled tiles are planned features and are clearly marked until implemented.")
        note.setObjectName("muted")
        root.addWidget(note)
