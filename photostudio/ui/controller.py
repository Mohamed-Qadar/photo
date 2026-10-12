"""EditorController — owns the active Document + History and exposes intents.

The UI calls these methods; they build Commands and push them on History.
Emits Qt signals so views refresh. Keeps UI code out of core/.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
from PySide6.QtCore import QObject, Signal, Slot, QThreadPool

from ..core import commands
from ..core.document import Document
from ..core.history import History
from ..core import project_io
from ..core.pipeline import composite
from ..imaging import io as img_io


class EditorController(QObject):
    processing_error = Signal(str)
    document_changed = Signal()       # structure/pixels changed -> re-render
    history_changed = Signal()        # undo/redo availability changed
    document_opened = Signal()        # a new document became active

    def __init__(self, parent=None):
        super().__init__(parent)
        self.document: Optional[Document] = None
        self.history: Optional[History] = None
        self.project_path: Optional[Path] = None
        self._dirty = False
        self._revision = 0
        self.processing_pool = QThreadPool(self)
        self.processing_pool.setMaxThreadCount(1)
        self._processing = None

    # ---- lifecycle ----------------------------------------------------
    def _attach(self, document: Document, path: Optional[Path] = None):
        self._revision += 1
        self.document = document
        self.history = History(on_change=self._on_history_change)
        self.project_path = path
        self._dirty = False
        self.document_opened.emit()
        self.document_changed.emit()
        self.history_changed.emit()

    def new_document(self, width: int, height: int, name: str = "Untitled",
                     background=(255, 255, 255, 255)):
        self._attach(Document.blank(width, height, name=name, background=background))

    def open_image(self, path: str | Path):
        pixels = img_io.load_image(path)
        name = Path(path).stem
        self._attach(Document.from_image(pixels, name=name))

    def open_project(self, path: str | Path):
        doc = project_io.load_project(path)
        self._attach(doc, path=Path(path))

    def open_template(self, key: str):
        from ..core import templates
        self._attach(templates.build(templates.get(key)))

    def import_svg(self, path: str | Path, max_size: int = 1024):
        """Rasterize an SVG via Qt and add it as an image layer (offline)."""
        if self.document is None:
            return
        from PySide6.QtCore import QRectF
        from PySide6.QtGui import QImage, QPainter
        from PySide6.QtSvg import QSvgRenderer
        renderer = QSvgRenderer(str(path))
        if not renderer.isValid():
            raise ValueError("Invalid or unreadable SVG")
        size = renderer.defaultSize()
        w = size.width() or max_size
        h = size.height() or max_size
        scale = min(max_size / max(w, 1), max_size / max(h, 1), 1.0)
        tw, th = max(1, int(w * scale)), max(1, int(h * scale))
        img = QImage(tw, th, QImage.Format.Format_RGBA8888)
        img.fill(0)
        painter = QPainter(img)
        renderer.render(painter, QRectF(0, 0, tw, th))
        painter.end()
        from .qimage_bridge import qimage_to_ndarray
        pixels = qimage_to_ndarray(img)
        from ..core.document import Layer
        layer = Layer(pixels=pixels, name=Path(path).stem)
        self._push(commands.AddLayerCommand(self.document, layer))

    # ---- persistence --------------------------------------------------
    def save_project(self, path: Optional[str | Path] = None):
        if self.document is None:
            return
        target = Path(path) if path else self.project_path
        if target is None:
            raise ValueError("No path to save to")
        project_io.save_project(self.document, target)
        self.project_path = target
        self._dirty = False
        self.history_changed.emit()

    def export(self, path: str | Path, fmt: str, **opts):
        if self.document is None:
            return
        project_io.export_document(self.document, path, fmt=fmt, **opts)

    def render(self, use_adjustments: bool = True) -> Optional[np.ndarray]:
        if self.document is None:
            return None
        return composite(self.document, use_adjustments=use_adjustments)

    # ---- editing intents ---------------------------------------------
    def _push(self, command):
        if self.history is None:
            return
        self._revision += 1
        self.history.push(command)
        self._dirty = True
        self.document_changed.emit()

    def set_adjustment(self, key: str, value: float):
        layer = self._active()
        if layer is None:
            return
        self._push(commands.AdjustmentCommand(layer, key, value))

    def crop(self, x: int, y: int, w: int, h: int):
        layer = self._active()
        if layer is None or layer.pixels is None:
            return
        self._push(commands.CropCommand(self.document, layer, x - layer.offset[0], y - layer.offset[1], w, h))

    def rotate_90(self, turns: int = 1):
        layer = self._active()
        if layer is None or layer.pixels is None:
            return
        self._push(commands.Rotate90Command(self.document, layer, turns))

    def flip(self, horizontal: bool):
        layer = self._active()
        if layer is None or layer.pixels is None:
            return
        self._push(commands.FlipCommand(self.document, layer, horizontal))

    def resize(self, width: int, height: int):
        layer = self._active()
        if layer is None or layer.pixels is None:
            return
        self._push(commands.ResizeCommand(self.document, layer, width, height))

    def add_text(self, text: str = "Double-click to edit", font_size: int = 48):
        if self.document is None:
            return
        w = min(self.document.width, max(200, len(text) * font_size // 2))
        layer = Document.make_text_layer(text, width=w, height=font_size * 2,
                                         font_size=font_size)
        layer.offset = (max(0, (self.document.width - w) // 2),
                        max(0, (self.document.height - font_size * 2) // 2))
        self._push(commands.AddLayerCommand(self.document, layer))

    def add_shape(self, shape: str = "rectangle"):
        if self.document is None:
            return
        size = max(40, min(self.document.width, self.document.height) // 3)
        layer = Document.make_shape_layer(shape, width=size, height=size)
        layer.offset = (max(0, (self.document.width - size) // 2),
                        max(0, (self.document.height - size) // 2))
        self._push(commands.AddLayerCommand(self.document, layer))

    def apply_filter(self, name: str):
        from ..imaging.filters import FILTERS
        layer = self._active()
        if layer is None or layer.pixels is None or name not in FILTERS:
            return
        func, kwargs = FILTERS[name]
        self._filter(layer, func, name, **kwargs)

    def apply_beauty(self, name: str):
        from ..imaging.beauty import BEAUTY_FILTERS
        layer = self._active()
        if layer is None or layer.pixels is None or name not in BEAUTY_FILTERS:
            return
        func, kwargs = BEAUTY_FILTERS[name]
        self._filter(layer, func, name, **kwargs)

    def heal_at(self, x: int, y: int, radius: int = 14):
        from ..imaging.beauty import heal
        layer = self._active()
        if layer is None or layer.pixels is None:
            return
        # Translate canvas (document) coords to layer-local coords.
        lx, ly = int(x) - layer.offset[0], int(y) - layer.offset[1]
        if not (0 <= lx < layer.width and 0 <= ly < layer.height):
            return
        self._filter(layer, heal, "Spot Removal", cx=lx, cy=ly, radius=radius)

    def _filter(self, layer, func, label, **kwargs):
        if layer.width * layer.height < 1_000_000:
            self._push(commands.FilterCommand(self.document, layer, func, label, **kwargs))
            return
        if self._processing is not None:
            self.processing_error.emit("An image operation is still running. Please wait.")
            return
        from .workers import Job
        pixels = layer.pixels
        self._processing = (self._revision, self.document, layer, label)
        job = Job(self._revision, lambda: func(pixels, **kwargs))
        job.signals.done.connect(self._finish_processing)
        self.processing_pool.start(job)

    @Slot(int, object, object)
    def _finish_processing(self, revision, result, error):
        pending = self._processing
        self._processing = None
        if pending is None:
            return
        _, doc, layer, label = pending
        if error:
            self.processing_error.emit(str(error))
        elif revision == self._revision and doc is self.document and not layer.locked:
            self._push(commands._PixelSwapCommand(doc, layer, result, False, label))
        else:
            self.processing_error.emit("Image operation discarded because the document changed.")

    def delete_active_layer(self):
        layer = self._active()
        if layer is None or self.document is None:
            return
        self._push(commands.RemoveLayerCommand(self.document, layer))

    def reorder_active(self, delta: int):
        layer = self._active()
        if layer and self.document:
            self._push(commands.ReorderLayerCommand(self.document, layer, delta))

    def duplicate_active(self):
        layer = self._active()
        if layer and self.document:
            self._push(commands.DuplicateLayerCommand(self.document, layer))

    def set_opacity(self, opacity: float):
        layer = self._active()
        if layer:
            self._push(commands.SetOpacityCommand(layer, opacity))

    def align_active(self, where: str):
        layer = self._active()
        if layer and self.document:
            self._push(commands.AlignCommand(self.document, layer, where))

    def set_text_property(self, key: str, value):
        layer = self._active()
        if layer and layer.kind.value == "text":
            self._push(commands.SetTextPropertyCommand(layer, key, value))

    def group_selected(self, layer_ids: list[str]):
        if self.document is None or len(layer_ids) < 2:
            return
        from ..core.document import new_id
        layers = [self.document.layer_by_id(i) for i in layer_ids]
        layers = [l for l in layers if l is not None and not l.locked]
        self._push(commands.GroupCommand(layers, new_id()))

    def ungroup_active(self):
        layer = self._active()
        if layer is None or layer.group is None or self.document is None:
            return
        members = [l for l in self.document.layers if l.group == layer.group]
        if any(l.locked for l in members):
            return
        self._push(commands.GroupCommand(members, None))

    def move_active_layer(self, x: int, y: int):
        layer = self._active()
        if layer is None:
            return
        if layer.group is not None and self.document is not None:
            dx, dy = int(x) - layer.offset[0], int(y) - layer.offset[1]
            members = [l for l in self.document.layers if l.group == layer.group]
            if any(l.locked for l in members):
                return
            self._push(commands.MoveGroupCommand(members, dx, dy))
        else:
            self._push(commands.MoveLayerCommand(layer, (int(x), int(y))))

    def set_text(self, text: str):
        layer = self._active()
        if layer is None or layer.kind.value != "text":
            return
        self._push(commands.SetTextCommand(layer, text))

    def replace_background(self, color=(255, 255, 255), tolerance: int = 40):
        from ..core.passport import replace_background
        layer = self._active()
        if layer is None or layer.pixels is None:
            return
        self._filter(layer, replace_background, "Replace Background",
                     new_color=color, tolerance=tolerance)

    def make_print_sheet(self, photo_size_key: str, sheet_key: str, dpi: int = 300):
        """Build a new print-sheet document from the current composite."""
        from ..core import passport
        if self.document is None:
            return
        photo = composite(self.document)
        psize = next(p for p in passport.PHOTO_SIZES if p.key == photo_size_key)
        sheet = next(s for s in passport.SHEET_SIZES if s.key == sheet_key)
        sheet_px = passport.build_print_sheet(photo, psize.width_mm, psize.height_mm,
                                              sheet, dpi=dpi)
        doc = Document.from_image(sheet_px, name=f"Sheet {sheet.key}", dpi=dpi)
        self._attach(doc)

    def export_pdf(self, path: str | Path):
        if self.document is None:
            return
        project_io.export_document(self.document, path, fmt="pdf")

    def undo(self):
        if self.history and self.history.can_undo():
            self._revision += 1
            self.history.undo()
            self._dirty = True
            self.document_changed.emit()

    def redo(self):
        if self.history and self.history.can_redo():
            self._revision += 1
            self.history.redo()
            self._dirty = True
            self.document_changed.emit()

    # ---- helpers ------------------------------------------------------
    def _active(self):
        layer = self.document.active_layer if self.document else None
        return layer if layer is not None and not layer.locked else None

    def _on_history_change(self):
        self._dirty = True
        self.history_changed.emit()

    @property
    def is_dirty(self) -> bool:
        return self._dirty

    @property
    def can_undo(self) -> bool:
        return bool(self.history and self.history.can_undo())

    @property
    def can_redo(self) -> bool:
        return bool(self.history and self.history.can_redo())
