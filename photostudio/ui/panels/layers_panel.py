"""Shared layer selection, editable names, thumbnails and drag ordering."""
from __future__ import annotations
import copy
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (QAbstractItemView, QHBoxLayout, QLabel, QListWidget,
                               QListWidgetItem, QPushButton, QSlider, QVBoxLayout, QWidget, QMenu)
from ..qimage_bridge import ndarray_to_qpixmap
from ..workers import RenderQueue
from ...imaging.transforms import resize


def thumbnails(doc, **kwargs):
    result = {}
    for layer in doc.layers:
        item = copy.copy(layer)
        ratio = min(64 / max(1, layer.width), 48 / max(1, layer.height), 1)
        w, h = max(1, round(layer.width*ratio)), max(1, round(layer.height*ratio))
        if item.pixels is not None:
            item.pixels = resize(item.pixels, w, h)
        else:
            item.spec = dict(layer.spec)
            item.spec.update(width=w, height=h)
            for key in ("font_size", "stroke_width", "outline_width", "shadow_offset"):
                if key in item.spec:
                    item.spec[key] = max(0, round(item.spec[key]*ratio))
            if "font_size" in item.spec:
                item.spec["font_size"] = max(1, item.spec["font_size"])
        item.scale_x = item.scale_y = 1
        px = item.render()
        ratio = min(64/px.shape[1], 48/px.shape[0], 1)
        result[layer.id] = resize(px, max(1, round(px.shape[1]*ratio)), max(1, round(px.shape[0]*ratio)))
    return result


class LayerList(QListWidget):
    def __init__(self, panel):
        super().__init__()
        self.panel = panel
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)

    def dropEvent(self, event):
        dragged = self.panel.selected_layer_ids()
        if any(self.panel.controller.document.layer_by_id(i).locked for i in dragged):
            event.ignore()
            return
        self.panel._syncing = True
        super().dropEvent(event)
        self.panel._syncing = False
        ids = [self.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.count())]
        self.panel.controller.reorder_layers(list(reversed(ids)), dragged)


class LayersPanel(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self._syncing = False
        self._icons = {}
        self._signature = None
        self.thumbnails = RenderQueue(self, thumbnails)
        self.thumbnails.ready.connect(self._set_thumbnails)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Layers"))
        self.list = LayerList(self)
        self.list.setIconSize(QSize(64, 48))
        self.list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.list.itemChanged.connect(self._item_changed)
        self.list.itemSelectionChanged.connect(self._selection_changed)
        self.list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list.customContextMenuRequested.connect(self._context_menu)
        layout.addWidget(self.list)
        row = QHBoxLayout()
        row.addWidget(QLabel("Opacity"))
        self.opacity = QSlider(Qt.Orientation.Horizontal)
        self.opacity.setRange(0, 100)
        self.opacity.valueChanged.connect(lambda v: controller.set_opacity(v/100))
        row.addWidget(self.opacity)
        layout.addLayout(row)
        row = QHBoxLayout()
        for name, slot in [("▲", lambda: controller.reorder_active(1)),
                           ("▼", lambda: controller.reorder_active(-1)),
                           ("Lock", self._toggle_lock),
                           ("Dup", controller.duplicate_selection),
                           ("Del", controller.delete_selection)]:
            button = QPushButton(name)
            button.setToolTip({"▲": "Bring forward", "▼": "Send backward", "Dup": "Duplicate selected layers",
                               "Del": "Delete selected layers"}.get(name, "Lock or unlock selected layers"))
            button.clicked.connect(slot)
            row.addWidget(button)
        layout.addLayout(row)
        controller.document_opened.connect(self._opened)
        controller.document_changed.connect(self.refresh)
        controller.selection_changed.connect(self._sync_selection)

    def _opened(self):
        self._signature = None
        self._icons = {}
        self.refresh()

    def selected_layer_ids(self):
        return [i.data(Qt.ItemDataRole.UserRole) for i in self.list.selectedItems()]

    def _sync_selection(self):
        self._syncing = True
        for row in range(self.list.count()):
            item = self.list.item(row)
            item.setSelected(item.data(Qt.ItemDataRole.UserRole) in self.controller.selected_ids)
        layer = self.controller.document.active_layer if self.controller.document else None
        self.opacity.blockSignals(True)
        self.opacity.setValue(round(layer.opacity*100) if layer else 100)
        self.opacity.setEnabled(layer is not None and not layer.locked)
        self.opacity.blockSignals(False)
        self._syncing = False

    def refresh(self):
        doc = self.controller.document
        self._syncing = True
        ids = [self.list.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.list.count())]
        expected = [l.id for l in reversed(doc.layers)] if doc else []
        if ids != expected:
            self.list.clear()
            for layer_id in expected:
                item = QListWidgetItem()
                item.setData(Qt.ItemDataRole.UserRole, layer_id)
                self.list.addItem(item)
        if doc:
            for row, layer in enumerate(reversed(doc.layers)):
                item = self.list.item(row)
                flags = item.flags() | Qt.ItemFlag.ItemIsUserCheckable
                if not layer.locked:
                    flags |= Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsDragEnabled
                else:
                    flags &= ~(Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsDragEnabled)
                item.setFlags(flags)
                item.setText(layer.name)
                item.setToolTip(f"{layer.kind.value} · {'Locked' if layer.locked else 'Unlocked'}" +
                                (" · Grouped" if layer.group else ""))
                item.setCheckState(Qt.CheckState.Checked if layer.visible else Qt.CheckState.Unchecked)
                item.setIcon(self._icons.get(layer.id, QIcon()))
            signature = [(l.id, id(l.pixels), repr(l.spec), l.rotation) for l in doc.layers]
            if signature != self._signature:
                self._signature = signature
                self.thumbnails.request(doc)
        self._syncing = False
        self._sync_selection()

    def _set_thumbnails(self, pixels):
        self._icons = {i: QIcon(ndarray_to_qpixmap(px)) for i, px in pixels.items()}
        self._syncing = True
        for row in range(self.list.count()):
            item = self.list.item(row)
            item.setIcon(self._icons.get(item.data(Qt.ItemDataRole.UserRole), QIcon()))
        self._syncing = False

    def _item_changed(self, item):
        if self._syncing:
            return
        layer_id = item.data(Qt.ItemDataRole.UserRole)
        layer = self.controller.document.layer_by_id(layer_id)
        if item.text() != layer.name:
            self.controller.rename_layer(layer_id, item.text())
        else:
            self.controller.set_visible(layer_id, item.checkState() == Qt.CheckState.Checked)

    def _selection_changed(self):
        if not self._syncing:
            self.controller.select(self.selected_layer_ids())

    def _toggle_lock(self):
        layers = self.controller.selected_layers(editable=False, expand_groups=False)
        lock = any(not l.locked for l in layers)
        for layer in layers:
            self.controller.set_locked(layer.id, lock)

    def _context_menu(self, pos):
        item = self.list.itemAt(pos)
        if item is None:
            return
        if not item.isSelected():
            self.controller.select([item.data(Qt.ItemDataRole.UserRole)])
        menu = QMenu(self)
        actions = [("Rename", lambda: self.list.editItem(item)),
                   ("Lock / Unlock", self._toggle_lock),
                   ("Group selected", lambda: self.controller.group_selected(self.selected_layer_ids())),
                   ("Ungroup", self.controller.ungroup_active),
                   ("Duplicate", self.controller.duplicate_selection),
                   ("Delete", self.controller.delete_selection)]
        layer = self.controller.document.layer_by_id(item.data(Qt.ItemDataRole.UserRole))
        for label, slot in actions:
            action = menu.addAction(label)
            action.triggered.connect(slot)
            if label in ("Rename", "Delete", "Duplicate"):
                action.setEnabled(not layer.locked)
        menu.exec(self.list.mapToGlobal(pos))
