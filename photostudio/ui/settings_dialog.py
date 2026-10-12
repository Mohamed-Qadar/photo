"""Settings dialog with General and About tabs.

The About tab carries the developer attribution required by the project brief.
"""
from __future__ import annotations
from .i18n import tr, source_text

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QComboBox, QDialog, QDialogButtonBox, QFormLayout,
                               QLabel, QTabWidget, QVBoxLayout, QWidget)

from .. import (__app_name__, __author__, __author_specialization__,
                __author_title__, __contact_email__, __github_url__, __version__)


class SettingsDialog(QDialog):
    theme_changed = Signal(bool)  # True = dark
    language_changed = Signal(str)

    def __init__(self, parent=None, dark: bool = True):
        super().__init__(parent)
        self.setWindowTitle(tr("Settings"))
        self.setMinimumWidth(460)
        layout = QVBoxLayout(self)

        tabs = QTabWidget()
        tabs.addTab(self._general_tab(dark), tr("General"))
        tabs.addTab(self._about_tab(), tr("About"))
        layout.addWidget(tabs)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.accept)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

    def _general_tab(self, dark: bool) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems([tr(item) for item in ["Dark", "Light"]])
        self.theme_combo.setCurrentIndex(0 if dark else 1)
        self.theme_combo.currentIndexChanged.connect(
            lambda i: self.theme_changed.emit(i == 0))
        form.addRow(tr("Theme:"), self.theme_combo)
        from . import i18n
        self.language_combo = QComboBox()
        self.language_combo.addItems([tr("English"), tr("Somali")])
        self.language_combo.setCurrentIndex(1 if i18n.LANGUAGE == "so" else 0)
        self.language_combo.currentIndexChanged.connect(
            lambda i: self.language_changed.emit("so" if i == 1 else "en"))
        form.addRow(tr("Language"), self.language_combo)
        return w

    def _about_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        text = QLabel(
            tr(f"<h3>{__app_name__}</h3>"
            f"<p>Version {__version__}<br>Offline-first photo &amp; design studio.</p>"
            "<hr>"
            f"<p><b>Developed by {__author__}</b><br>"
            f"{__author_title__}<br>"
            f"Specializing in {__author_specialization__}.</p>"
            f"<p>Contact: <a href='mailto:{__contact_email__}'>{__contact_email__}</a><br>"
            f"GitHub: <a href='{__github_url__}'>{__github_url__}</a></p>"))
        text.setTextFormat(Qt.TextFormat.RichText)
        text.setOpenExternalLinks(True)
        text.setWordWrap(True)
        layout.addWidget(text)
        layout.addStretch(1)
        return w
