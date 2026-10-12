"""EditorController — owns the active Document + History and exposes intents.

The UI calls these methods; they build Commands and push them on History.
Emits Qt signals so views refresh. Keeps UI code out of core/.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
from PySide6.QtCore import QObject, Signal

from ..core import commands
from ..core.document import Document
from ..core.history import History
from ..core import project_io
from ..core.pipeline import composite
from ..imaging import io as img_io


class EditorController(QObject):
    document_changed = Signal()       # structure/pixels changed -> re-render
    history_changed = Signal()        # undo/redo availability changed
    document_opened = Signal()        # a new document became active

    def __init__(self, parent=None):
        super().__init__(parent)
        self.document: Optional[Document] = None
        self.history: Optional[History] = None
        self.project_path: Optional[Path] = None
        self._dirty = False

    # ---- lifecycle ----------------------------------------------------
    def _attach(self, document: Document, path: Optional[Path] = None):
        self.document = document
        self.history = History(on_change=self._on_history_change)
        self.project_path = path
        self._dirty = False
        self.document_opened.emit()
        self.document_changed.emit()
        self.history_changed.emit()

    def new_document(self, width: int, height: int, name: str = "Untitled"):
        from ..core.document import Document as Doc, Layer, blank_pixels
        layer = Layer(pixels=blank_pixels(width, height), name="Background")
        self._attach(Doc(width=width, height=height, layers=[layer], name=name))

    def open_image(self, path: str | Path):
        pixels = img_io.load_image(path)
        name = Path(path).stem
        self._attach(Document.from_image(pixels, name=name))

    def open_project(self, path: str | Path):
        doc = project_io.load_project(path)
        self._attach(doc, path=Path(path))

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

    def render(self) -> Optional[np.ndarray]:
        if self.document is None:
            return None
        return composite(self.document)

    # ---- editing intents ---------------------------------------------
    def _push(self, command):
        if self.history is None:
            return
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
        if layer is None:
            return
        self._push(commands.CropCommand(self.document, layer, x, y, w, h))

    def rotate_90(self, turns: int = 1):
        layer = self._active()
        if layer is None:
            return
        self._push(commands.Rotate90Command(self.document, layer, turns))

    def flip(self, horizontal: bool):
        layer = self._active()
        if layer is None:
            return
        self._push(commands.FlipCommand(self.document, layer, horizontal))

    def resize(self, width: int, height: int):
        layer = self._active()
        if layer is None:
            return
        self._push(commands.ResizeCommand(self.document, layer, width, height))

    def undo(self):
        if self.history and self.history.can_undo():
            self.history.undo()
            self._dirty = True
            self.document_changed.emit()

    def redo(self):
        if self.history and self.history.can_redo():
            self.history.redo()
            self._dirty = True
            self.document_changed.emit()

    # ---- helpers ------------------------------------------------------
    def _active(self):
        return self.document.active_layer if self.document else None

    def _on_history_change(self):
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
