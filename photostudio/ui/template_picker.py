"""Offline template gallery: streamed thumbnails, filters and a large preview."""
import threading
import queue
from .i18n import tr
from PySide6.QtCore import Qt, QSize, QThreadPool, Slot, QObject, Signal, QRunnable, QRect
from PySide6.QtGui import QIcon, QColor, QFont
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QListWidget,
                               QListWidgetItem, QAbstractItemView, QComboBox, QLabel,
                               QPushButton, QSplitter, QWidget, QStyledItemDelegate, QStyle)
from ..core import templates
from ..core.pipeline import composite_preview
from .qimage_bridge import ndarray_to_qpixmap

_CACHE = {}  # At most 62 bounded previews, reused when reopening the gallery.


def gallery_previews():
    return {t.key: composite_preview(templates.build(t), max_side=480) for t in templates.TEMPLATES}


class PreviewSignals(QObject):
    ready = Signal(str, object)
    failed = Signal(str)


class GalleryWorker(QRunnable):
    def __init__(self, catalogue, signals, cancelled, priority):
        super().__init__()
        self.catalogue, self.signals, self.cancelled = catalogue, signals, cancelled
        self.priority = priority

    def run(self):
        pending = {template.key:template for template in self.catalogue}
        while pending:
            if self.cancelled.is_set(): return
            try:
                key = self.priority.get_nowait()
            except queue.Empty:
                key = next(iter(pending))
            template = pending.pop(key,None)
            if template is None: continue
            try:
                pixels = composite_preview(templates.build(template), max_side=480)
                self.signals.ready.emit(template.key, pixels)
            except Exception as exc:
                self.signals.failed.emit(str(exc))


class TemplateCard(QStyledItemDelegate):
    def paint(self, painter, option, index):
        painter.save()
        rect = option.rect.adjusted(5, 5, -5, -5)
        selected = bool(option.state & QStyle.StateFlag.State_Selected)
        palette = option.palette
        painter.setBrush(palette.highlight() if selected else palette.base())
        painter.setPen(palette.highlight().color() if selected else palette.mid().color())
        painter.drawRoundedRect(rect, 8, 8)
        area = QRect(rect.x()+10, rect.y()+10, rect.width()-20, 166)
        icon = index.data(Qt.ItemDataRole.DecorationRole)
        if icon:
            pixmap = icon.pixmap(QSize(480,480))
            pixmap = pixmap.scaled(area.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            painter.drawPixmap(area.center().x()-pixmap.width()//2, area.center().y()-pixmap.height()//2, pixmap)
        painter.setPen(palette.highlightedText().color() if selected else palette.text().color())
        font = QFont(option.font)
        font.setWeight(QFont.Weight.DemiBold)
        painter.setFont(font)
        painter.drawText(QRect(rect.x()+10,rect.y()+183,rect.width()-20,58),
                         Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap, index.data())
        painter.restore()

    def sizeHint(self, option, index):
        return QSize(218,254)


class TemplatePicker(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.priority = queue.Queue()
        self.setWindowTitle(tr("Offline templates"))
        self.resize(1050, 720)
        layout = QVBoxLayout(self)
        filters = QHBoxLayout()
        layout.addLayout(filters)
        self.search = QLineEdit()
        self.search.setPlaceholderText(tr("Search name or category…"))
        filters.addWidget(self.search, 1)
        self.category = QComboBox()
        self.category.setMinimumContentsLength(16)
        self.category.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.category.addItem(tr("All categories"), "")
        for category in templates.by_category():
            self.category.addItem(tr(category), category)
        filters.addWidget(self.category)
        splitter = QSplitter()
        layout.addWidget(splitter,1)
        self.list = QListWidget()
        self.list.setItemDelegate(TemplateCard(self.list))
        self.list.setViewMode(QListWidget.ViewMode.IconMode)
        self.list.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.list.setMovement(QListWidget.Movement.Static)
        self.list.setGridSize(QSize(218,254))
        self.list.setWordWrap(True)
        self.list.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        splitter.addWidget(self.list)
        detail = QWidget()
        detail.setMinimumWidth(220)
        panel = QVBoxLayout(detail)
        self.preview = QLabel(tr("Rendering preview…"))
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setMinimumSize(200,240)
        panel.addWidget(self.preview,1)
        self.details = QLabel()
        self.details.setWordWrap(True)
        panel.addWidget(self.details)
        hint = QLabel(tr("Double-click text to edit. Click a photo to replace it. Drag to move."))
        hint.setWordWrap(True)
        panel.addWidget(hint)
        splitter.addWidget(detail)
        splitter.setSizes([700,300])
        self.items = {}
        for template in templates.TEMPLATES:
            item = QListWidgetItem(tr(template.name))
            item.setData(Qt.ItemDataRole.UserRole, template.key)
            item.setData(257, f"{template.name} {template.category}")
            item.setData(258, template.category)
            item.setToolTip(f"{tr(template.name)}\n{tr(template.category)} · {template.width} × {template.height}")
            self.list.addItem(item)
            self.items[template.key] = item
        row = QHBoxLayout()
        layout.addLayout(row)
        self.count = QLabel()
        row.addWidget(self.count,1)
        cancel = QPushButton(tr("Cancel"))
        cancel.setMinimumHeight(36)
        cancel.clicked.connect(self.reject)
        row.addWidget(cancel)
        self.use_button = QPushButton(tr("Use Template"))
        self.use_button.setObjectName("primary")
        self.use_button.setMinimumHeight(36)
        self.use_button.setDefault(True)
        self.use_button.clicked.connect(self.accept)
        row.addWidget(self.use_button)
        self.list.currentItemChanged.connect(self._selection_changed)
        self.list.itemDoubleClicked.connect(lambda item: self.accept())
        self.search.textChanged.connect(self._filter)
        self.category.currentIndexChanged.connect(lambda _: self._filter(self.search.text()))
        self.list.setCurrentRow(0)
        self._filter("")
        self.cancelled = threading.Event()
        self.signals = PreviewSignals()
        self.signals.ready.connect(self._preview_ready)
        self.signals.failed.connect(lambda message: self.count.setText(tr("Could not render preview")+": "+message))
        self.pool = QThreadPool(self)
        self.pool.setMaxThreadCount(1)
        missing = []
        for template in templates.TEMPLATES:
            if template.key in _CACHE:
                self._preview_ready(template.key,_CACHE[template.key])
            else:
                missing.append(template)
        self.pool.start(GalleryWorker(missing,self.signals,self.cancelled,self.priority))

    @Slot(str, object)
    def _preview_ready(self, key, pixels):
        _CACHE[key] = pixels
        self.items[key].setIcon(QIcon(ndarray_to_qpixmap(pixels)))
        if key == self.selected_key(): self._selection_changed()

    def _selection_changed(self, *args):
        key = self.selected_key()
        self.use_button.setEnabled(key is not None)
        if key is None:
            self.preview.clear()
            self.details.setText(tr("No matching templates"))
            return
        template = templates.get(key)
        self.details.setText(f"{tr(template.name)}\n{tr(template.category)}\n{template.width} × {template.height} px · {template.dpi} DPI")
        if key in _CACHE:
            self.preview.setPixmap(ndarray_to_qpixmap(_CACHE[key]).scaled(
                max(1,self.preview.width()),max(1,self.preview.height()),Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation))
        else:
            self.priority.put(key)
            self.preview.setText(tr("Rendering preview…"))

    def resizeEvent(self,event):
        super().resizeEvent(event)
        if hasattr(self,"use_button"): self._selection_changed()

    def _filter(self, text):
        category = self.category.currentData()
        visible = []
        for item in self.items.values():
            show = (not category or item.data(258)==category) and text.casefold() in (item.text()+" "+item.data(257)).casefold()
            item.setHidden(not show)
            if show: visible.append(item)
        if self.selected_key() is None:
            self.list.setCurrentItem(visible[0] if visible else None)
        self.count.setText(f"{len(visible)} / {len(self.items)}")
        self._selection_changed()

    def selected_key(self):
        item = self.list.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item and not item.isHidden() else None

    def accept(self):
        if self.selected_key() is not None: super().accept()

    def done(self, result):
        self.cancelled.set()
        self.pool.waitForDone()
        super().done(result)
