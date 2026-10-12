"""Offline searchable template gallery with bounded previews."""
from PySide6.QtCore import Qt, QSize, QThreadPool, Slot
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLineEdit, QListWidget,
                               QListWidgetItem, QDialogButtonBox, QAbstractItemView)
from ..core import templates
from ..core.pipeline import composite_preview
from .qimage_bridge import ndarray_to_qpixmap
from .workers import Job


def gallery_previews():
    return {t.key: composite_preview(templates.build(t), max_side=160) for t in templates.TEMPLATES}


class TemplatePicker(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Offline templates")
        self.resize(720, 560)
        layout = QVBoxLayout(self)
        search = QLineEdit()
        search.setPlaceholderText("Search name or category…")
        layout.addWidget(search)
        self.list = QListWidget()
        self.list.setViewMode(QListWidget.ViewMode.IconMode)
        self.list.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.list.setMovement(QListWidget.Movement.Static)
        self.list.setIconSize(QSize(140, 160))
        self.list.setGridSize(QSize(205, 215))
        self.list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        layout.addWidget(self.list)
        for template in templates.TEMPLATES:
            item = QListWidgetItem(f"{template.name}\n{template.category}")
            item.setData(Qt.ItemDataRole.UserRole, template.key)
            self.list.addItem(item)
        self.list.setCurrentRow(0)
        search.textChanged.connect(lambda text: self._filter(text))
        self.list.itemDoubleClicked.connect(lambda item: self.accept())
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Open | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.pool = QThreadPool(self)
        self.pool.setMaxThreadCount(1)
        job = Job(0, gallery_previews)
        job.signals.done.connect(self._previews_ready)
        self.pool.start(job)

    @Slot(int, object, object)
    def _previews_ready(self, revision, previews, error):
        if error:
            return
        for row in range(self.list.count()):
            item = self.list.item(row)
            item.setIcon(QIcon(ndarray_to_qpixmap(previews[item.data(Qt.ItemDataRole.UserRole)])))

    def done(self, result):
        self.pool.waitForDone()
        super().done(result)

    def _filter(self, text):
        for row in range(self.list.count()):
            item = self.list.item(row)
            item.setHidden(text.casefold() not in item.text().casefold())

    def selected_key(self):
        item = self.list.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item and not item.isHidden() else None
