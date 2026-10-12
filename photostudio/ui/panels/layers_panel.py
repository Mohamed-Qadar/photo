"""Layers panel — list (multi-select), visibility, lock, opacity, and actions."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QAbstractItemView, QHBoxLayout, QLabel, QListWidget,
                               QListWidgetItem, QPushButton, QSlider, QVBoxLayout,
                               QWidget)

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
        self.list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.list.itemChanged.connect(self._on_item_changed)
        self.list.currentRowChanged.connect(self._on_row_selected)
        layout.addWidget(self.list)

        # Opacity
        op_row = QHBoxLayout()
        op_row.addWidget(QLabel("Opacity"))
        self.opacity = QSlider(Qt.Orientation.Horizontal)
        self.opacity.setRange(0, 100)
        self.opacity.setValue(100)
        self.opacity.valueChanged.connect(
            lambda v: self.controller.set_opacity(v / 100.0))
        op_row.addWidget(self.opacity)
        layout.addLayout(op_row)

        # Action buttons
        btns = QHBoxLayout()
        for text, slot in [("▲", lambda: self.controller.reorder_active(1)),
                           ("▼", lambda: self.controller.reorder_active(-1)),
                           ("Lock", self._toggle_lock),
                           ("Dup", self.controller.duplicate_active),
                           ("Del", self.controller.delete_active_layer)]:
            b = QPushButton(text)
            b.clicked.connect(slot)
            btns.addWidget(b)
        layout.addLayout(btns)

        controller.document_changed.connect(self.refresh)
        controller.document_opened.connect(self.refresh)
        self._syncing = False

    def selected_layer_ids(self):
        return [i.data(Qt.ItemDataRole.UserRole) for i in self.list.selectedItems()]

    def _toggle_lock(self):
        layer = self.controller.document.active_layer if self.controller.document else None
        if layer and self.controller.history:
            self.controller.history.push(commands.SetLayerLockCommand(layer, not layer.locked))
            self.controller.document_changed.emit()

    def refresh(self):
        doc = self.controller.document
        self._syncing = True
        self.list.clear()
        if doc is not None:
            for layer in reversed(doc.layers):  # top layer first
                mark = "🔒 " if layer.locked else ""
                grp = "  ⛓" if layer.group else ""
                item = QListWidgetItem(f"{mark}{layer.name}{grp}")
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Checked if layer.visible
                                   else Qt.CheckState.Unchecked)
                item.setData(Qt.ItemDataRole.UserRole, layer.id)
                self.list.addItem(item)
                if layer.id == doc.active_layer_id:
                    item.setSelected(True)
            active = doc.active_layer
            if active is not None:
                self.opacity.blockSignals(True)
                self.opacity.setValue(int(active.opacity * 100))
                self.opacity.blockSignals(False)
        self._syncing = False

    def _on_item_changed(self, item: QListWidgetItem):
        if self._syncing or self.controller.document is None:
            return
        layer = self.controller.document.layer_by_id(item.data(Qt.ItemDataRole.UserRole))
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
            active = self.controller.document.active_layer
            if active is not None:
                self.opacity.blockSignals(True)
                self.opacity.setValue(int(active.opacity * 100))
                self.opacity.blockSignals(False)
