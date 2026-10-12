"""Zoomable / pannable canvas built on QGraphicsView.

Renders the flattened pipeline output and supports an interactive crop overlay.
"""
from __future__ import annotations

from typing import Optional

import numpy as np
from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QPainter, QPen
from PySide6.QtWidgets import (QGraphicsPixmapItem, QGraphicsRectItem,
                               QGraphicsScene, QGraphicsView)

from .qimage_bridge import ndarray_to_qpixmap


class CanvasView(QGraphicsView):
    crop_committed = Signal(int, int, int, int)  # x, y, w, h in image pixels
    zoom_changed = Signal(float)

    MIN_SCALE = 0.02
    MAX_SCALE = 32.0

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.setRenderHints(QPainter.RenderHint.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setBackgroundBrush(QColor("#15171c"))

        self._pixmap_item: Optional[QGraphicsPixmapItem] = None
        self._scale = 1.0

        # crop state
        self._crop_mode = False
        self._crop_item: Optional[QGraphicsRectItem] = None
        self._crop_origin: Optional[QPointF] = None

    # ---- image display ------------------------------------------------
    def set_image(self, pixels: np.ndarray, reset_view: bool = False) -> None:
        pixmap = ndarray_to_qpixmap(pixels)
        if self._pixmap_item is None:
            self._pixmap_item = self._scene.addPixmap(pixmap)
            reset_view = True
        else:
            self._pixmap_item.setPixmap(pixmap)
        self._scene.setSceneRect(QRectF(pixmap.rect()))
        if reset_view:
            self.fit_to_window()

    def fit_to_window(self) -> None:
        if self._pixmap_item is None:
            return
        self.fitInView(self._pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)
        self._scale = self.transform().m11()
        self.zoom_changed.emit(self._scale)

    def set_zoom(self, scale: float) -> None:
        scale = max(self.MIN_SCALE, min(self.MAX_SCALE, scale))
        self.resetTransform()
        self.scale(scale, scale)
        self._scale = scale
        self.zoom_changed.emit(scale)

    def zoom_in(self):
        self.set_zoom(self._scale * 1.25)

    def zoom_out(self):
        self.set_zoom(self._scale / 1.25)

    def wheelEvent(self, event):
        if event.angleDelta().y() == 0:
            return
        factor = 1.25 if event.angleDelta().y() > 0 else 1 / 1.25
        new_scale = max(self.MIN_SCALE, min(self.MAX_SCALE, self._scale * factor))
        self.resetTransform()
        self.scale(new_scale, new_scale)
        self._scale = new_scale
        self.zoom_changed.emit(new_scale)

    # ---- crop interaction --------------------------------------------
    def begin_crop(self) -> None:
        if self._pixmap_item is None:
            return
        self._crop_mode = True
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setCursor(Qt.CursorShape.CrossCursor)

    def cancel_crop(self) -> None:
        self._crop_mode = False
        self._clear_crop_item()
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.unsetCursor()

    def _clear_crop_item(self):
        if self._crop_item is not None:
            self._scene.removeItem(self._crop_item)
            self._crop_item = None
        self._crop_origin = None

    def mousePressEvent(self, event):
        if self._crop_mode and event.button() == Qt.MouseButton.LeftButton:
            self._crop_origin = self.mapToScene(event.position().toPoint())
            self._clear_crop_item()
            self._crop_item = QGraphicsRectItem(QRectF(self._crop_origin, self._crop_origin))
            pen = QPen(QColor("#5b8cff"), 0)
            pen.setCosmetic(True)
            pen.setStyle(Qt.PenStyle.DashLine)
            self._crop_item.setPen(pen)
            self._crop_item.setBrush(QBrush(QColor(91, 140, 255, 40)))
            self._scene.addItem(self._crop_item)
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._crop_mode and self._crop_origin is not None and self._crop_item:
            current = self.mapToScene(event.position().toPoint())
            self._crop_item.setRect(QRectF(self._crop_origin, current).normalized())
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._crop_mode and self._crop_origin is not None and self._crop_item:
            rect = self._crop_item.rect().normalized()
            bounds = self._pixmap_item.boundingRect()
            rect = rect.intersected(bounds)
            self.cancel_crop()
            if rect.width() >= 1 and rect.height() >= 1:
                self.crop_committed.emit(
                    int(rect.x()), int(rect.y()),
                    int(rect.width()), int(rect.height()))
            return
        super().mouseReleaseEvent(event)
