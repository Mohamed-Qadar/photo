"""Layers panel — lists layers top-to-bottom; toggles visibility."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QVBoxLayout, QLabel, QWidget

from ..controller import EditorController
from ...core import commands


class LayersPanel(QWidget):
    def __init__(self, controller: EditorController):
        super().__init__()
        self.controller = controller
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        title = QLabel("Layers")
        title.setStyleSheet("font-weight:600;")
        layout.addWidget(title)

        self.list = QListWidget()
        self.list.itemChanged.connect(self._on_item_changed)
        self.list.currentRowChanged.connect(self._on_row_selected)
        layout.addWidget(self.list)

        controller.document_changed.connect(self.refresh)
        controller.document_opened.connect(self.refresh)
        self._syncing = False

    def refresh(self):
        doc = self.controller.document
        self._syncing = True
        self.list.clear()
        if doc is not None:
            for layer in reversed(doc.layers):  # top layer first
                item = QListWidgetItem(layer.name)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Checked if layer.visible
                                   else Qt.CheckState.Unchecked)
                item.setData(Qt.ItemDataRole.UserRole, layer.id)
                self.list.addItem(item)
        self._syncing = False

    def _on_item_changed(self, item: QListWidgetItem):
        if self._syncing or self.controller.document is None:
            return
        layer_id = item.data(Qt.ItemDataRole.UserRole)
        layer = self.controller.document.layer_by_id(layer_id)
        if layer is None:
            return
        visible = item.checkState() == Qt.CheckState.Checked
        if visible != layer.visible:
            self.controller.history.push(commands.SetLayerVisibilityCommand(layer, visible))
            self.controller.document_changed.emit()

    def _on_row_selected(self, row: int):
        if self._syncing or row < 0 or self.controller.document is None:
            return
        item = self.list.item(row)
        if item:
            self.controller.document.active_layer_id = item.data(Qt.ItemDataRole.UserRole)
