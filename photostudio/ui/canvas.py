"""Zoomable / pannable canvas built on QGraphicsView.

Renders the flattened pipeline output and supports an interactive crop overlay.
"""
from __future__ import annotations

from typing import Optional
import math

import numpy as np
from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QPainter, QPen
from PySide6.QtWidgets import (QGraphicsPixmapItem, QGraphicsRectItem,
                               QGraphicsScene, QGraphicsView)

from .qimage_bridge import ndarray_to_qpixmap


class CanvasView(QGraphicsView):
    crop_committed = Signal(int, int, int, int)  # x, y, w, h in image pixels
    point_clicked = Signal(int, int)             # x, y in image pixels (tools)
    zoom_changed = Signal(float)

    MIN_SCALE = 0.02
    MAX_SCALE = 32.0

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.setRenderHints(QPainter.RenderHint.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setBackgroundBrush(QColor("#15171c"))

        self._pixmap_item: Optional[QGraphicsPixmapItem] = None
        self._scale = 1.0
        self.controller = None
        self._gesture = None
        self._space = False
        self._pan_origin = None
        self._marquee = None
        self.snap_enabled = True
        self.read_only = False
        self._snap_guides = []
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)

        # crop state
        self._crop_mode = False
        self._crop_item: Optional[QGraphicsRectItem] = None
        self._crop_origin: Optional[QPointF] = None
        self._point_mode = False  # click-to-act tools (e.g. spot removal)
        self._guide_items = []

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
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.unsetCursor()

    def _clear_crop_item(self):
        if self._crop_item is not None:
            self._scene.removeItem(self._crop_item)
            self._crop_item = None
        self._crop_origin = None

    def set_face_guides(self, show: bool) -> None:
        """Draw/clear passport face-alignment guides (crown / eye-line / chin)."""
        for item in self._guide_items:
            self._scene.removeItem(item)
        self._guide_items = []
        if not show or self._pixmap_item is None:
            return
        rect = self._pixmap_item.boundingRect()
        w, h = rect.width(), rect.height()
        pen = QPen(QColor("#5b8cff"), 0)
        pen.setCosmetic(True)
        pen.setStyle(Qt.PenStyle.DashLine)
        from PySide6.QtWidgets import QGraphicsLineItem
        for frac in (0.12, 0.45, 0.85):   # crown, eye line, chin
            line = QGraphicsLineItem(0, h * frac, w, h * frac)
            line.setPen(pen)
            self._scene.addItem(line)
            self._guide_items.append(line)
        vline = QGraphicsLineItem(w / 2, 0, w / 2, h)
        vline.setPen(pen)
        self._scene.addItem(vline)
        self._guide_items.append(vline)

    def begin_point_tool(self) -> None:
        if self._pixmap_item is None:
            return
        self._point_mode = True
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setCursor(Qt.CursorShape.CrossCursor)

    def end_point_tool(self) -> None:
        self._point_mode = False
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.unsetCursor()

    def _tool_press(self, event):
        if self._point_mode and event.button() == Qt.MouseButton.LeftButton:
            p = self.mapToScene(event.position().toPoint())
            self.point_clicked.emit(int(p.x()), int(p.y()))
            return
        if self._crop_mode and event.button() == Qt.MouseButton.LeftButton:
            self._clear_crop_item()
            self._crop_origin = self.mapToScene(event.position().toPoint())
            self._crop_item = QGraphicsRectItem(QRectF(self._crop_origin, self._crop_origin))
            pen = QPen(QColor("#5b8cff"), 0)
            pen.setCosmetic(True)
            pen.setStyle(Qt.PenStyle.DashLine)
            self._crop_item.setPen(pen)
            self._crop_item.setBrush(QBrush(QColor(91, 140, 255, 40)))
            self._scene.addItem(self._crop_item)
            return
        super().mousePressEvent(event)

    def _tool_move(self, event):
        if self._crop_mode and self._crop_origin is not None and self._crop_item:
            current = self.mapToScene(event.position().toPoint())
            self._crop_item.setRect(QRectF(self._crop_origin, current).normalized())
            return
        super().mouseMoveEvent(event)

    def _tool_release(self, event):
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

    def bind_controller(self, controller):
        self.controller = controller
        controller.selection_changed.connect(self.viewport().update)
        controller.document_changed.connect(self.viewport().update)
        controller.document_opened.connect(self.cancel_gesture)

    def layer_rect(self, layer):
        w, h = layer.display_size
        return QRectF(*layer.offset, w, h)

    def selection_rect(self):
        if self.controller is None:
            return QRectF()
        rect = QRectF()
        for layer in self.controller.selected_layers(editable=False):
            rect = rect.united(self.layer_rect(layer))
        return rect

    def handle_positions(self):
        rect = self.selection_rect()
        if rect.isEmpty():
            return {}
        return {"nw": rect.topLeft(), "n": QPointF(rect.center().x(), rect.top()),
                "ne": rect.topRight(), "e": QPointF(rect.right(), rect.center().y()),
                "se": rect.bottomRight(), "s": QPointF(rect.center().x(), rect.bottom()),
                "sw": rect.bottomLeft(), "w": QPointF(rect.left(), rect.center().y()),
                "rotate": QPointF(rect.center().x(), rect.top() - 28 / self._scale)}

    def _handle_at(self, point):
        if not self.controller or not self.controller.selected_layers():
            return None
        for name, pos in self.handle_positions().items():
            if abs(point.x() - pos.x()) <= 6 / self._scale and abs(point.y() - pos.y()) <= 6 / self._scale:
                return name
        return None

    def drawForeground(self, painter, rect):
        super().drawForeground(painter, rect)
        if not self.controller or self.read_only:
            return
        painter.save()
        pen = QPen(QColor("#5b8cff"), 1)
        pen.setCosmetic(True)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        for layer in self.controller.selected_layers(editable=False):
            painter.drawRect(self.layer_rect(layer))
        selection = self.selection_rect()
        if not selection.isEmpty():
            painter.drawRect(selection)
            if self.controller.selected_layers():
                size = 8 / self._scale
                for name, pos in self.handle_positions().items():
                    painter.setBrush(QColor("#ffffff"))
                    if name == "rotate":
                        painter.drawLine(QPointF(selection.center().x(), selection.top()), pos)
                        painter.drawEllipse(pos, size / 2, size / 2)
                    else:
                        painter.drawRect(QRectF(pos.x()-size/2, pos.y()-size/2, size, size))
        painter.setBrush(QColor(91, 140, 255, 30))
        if self._marquee is not None:
            painter.drawRect(self._marquee.normalized())
        pen.setColor(QColor("#efb54a"))
        painter.setPen(pen)
        doc = self.controller.document
        if doc:
            for axis, value in self._snap_guides:
                if axis == "x":
                    painter.drawLine(QPointF(value, 0), QPointF(value, doc.height))
                else:
                    painter.drawLine(QPointF(0, value), QPointF(doc.width, value))
        painter.restore()

    def _hit_layer(self, point):
        doc = self.controller.document if self.controller else None
        if doc:
            for layer in reversed(doc.layers):
                if layer.visible and not layer.locked and layer.opacity > 0 and self.layer_rect(layer).contains(point):
                    return layer
        return None

    def mousePressEvent(self, event):
        self.setFocus()
        point = self.mapToScene(event.position().toPoint())
        if self._space or event.button() == Qt.MouseButton.MiddleButton:
            self._pan_origin = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            return
        if self.read_only:
            return
        if self._crop_mode or self._point_mode:
            return self._tool_press(event)
        if event.button() != Qt.MouseButton.LeftButton or not self.controller:
            return super().mousePressEvent(event)
        handle = self._handle_at(point)
        shift = bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
        layer = self._hit_layer(point)
        if not handle and layer:
            ids = list(self.controller.selected_ids)
            if shift:
                ids.remove(layer.id) if layer.id in ids else ids.append(layer.id)
                self.controller.select(ids)
                return
            if layer.id not in ids:
                self.controller.select([layer.id])
        elif not handle:
            if not shift:
                self.controller.select([])
            self._marquee = QRectF(point, point)
            self._marquee_start = point
            self._marquee_ids = list(self.controller.selected_ids)
            return
        layers = self.controller.selected_layers()
        if layers:
            from ..core.commands import transform_state
            self._gesture = {"mode": handle or "move", "origin": point,
                             "before": {l.id: transform_state(l) for l in layers},
                             "layers": layers, "rect": self.selection_rect()}

    def _snap_delta(self, dx, dy, rect, layers):
        self._snap_guides = []
        if not self.snap_enabled:
            return dx, dy
        doc = self.controller.document
        moving = rect.translated(dx, dy)
        x_targets, y_targets = [0, doc.width/2, doc.width], [0, doc.height/2, doc.height]
        ids = {l.id for l in layers}
        for layer in doc.layers:
            if layer.id not in ids and layer.visible:
                r = self.layer_rect(layer)
                x_targets += [r.left(), r.center().x(), r.right()]
                y_targets += [r.top(), r.center().y(), r.bottom()]
        for axis, values, targets in [("x", [moving.left(), moving.center().x(), moving.right()], x_targets),
                                       ("y", [moving.top(), moving.center().y(), moving.bottom()], y_targets)]:
            correction, target = min(((t-v, t) for t in targets for v in values), key=lambda pair: abs(pair[0]))
            if abs(correction) <= 7 / self._scale:
                self._snap_guides.append((axis, target))
                if axis == "x":
                    dx += correction
                else:
                    dy += correction
        return round(dx), round(dy)

    def mouseMoveEvent(self, event):
        point = self.mapToScene(event.position().toPoint())
        if self._pan_origin is not None:
            delta = event.position() - self._pan_origin
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - round(delta.x()))
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - round(delta.y()))
            self._pan_origin = event.position()
            return
        if self._crop_mode or self._point_mode:
            return self._tool_move(event)
        if self._marquee is not None:
            self._marquee = QRectF(self._marquee_start, point)
            self.viewport().update()
            return
        if not self._gesture:
            handle = self._handle_at(point)
            cursors = {"nw": Qt.CursorShape.SizeFDiagCursor, "se": Qt.CursorShape.SizeFDiagCursor,
                       "ne": Qt.CursorShape.SizeBDiagCursor, "sw": Qt.CursorShape.SizeBDiagCursor,
                       "n": Qt.CursorShape.SizeVerCursor, "s": Qt.CursorShape.SizeVerCursor,
                       "e": Qt.CursorShape.SizeHorCursor, "w": Qt.CursorShape.SizeHorCursor,
                       "rotate": Qt.CursorShape.CrossCursor}
            self.setCursor(cursors.get(handle, Qt.CursorShape.OpenHandCursor if self._space else Qt.CursorShape.ArrowCursor))
            return
        from ..core.commands import set_transform
        g = self._gesture
        dx, dy = point.x() - g["origin"].x(), point.y() - g["origin"].y()
        r, mode = g["rect"], g["mode"]
        for layer in g["layers"]:
            set_transform(layer, g["before"][layer.id])
        if mode == "move":
            dx, dy = self._snap_delta(dx, dy, r, g["layers"])
            for layer in g["layers"]:
                layer.offset = (round(layer.offset[0] + dx), round(layer.offset[1] + dy))
        elif mode == "rotate":
            center = r.center()
            a0 = math.atan2(g["origin"].y()-center.y(), g["origin"].x()-center.x())
            a1 = math.atan2(point.y()-center.y(), point.x()-center.x())
            angle = math.degrees(a1-a0)
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                angle = round(angle/15)*15
            radians = math.radians(angle)
            for layer in g["layers"]:
                lc = self.layer_rect(layer).center() - center
                new_center = center + QPointF(lc.x()*math.cos(radians)-lc.y()*math.sin(radians),
                                             lc.x()*math.sin(radians)+lc.y()*math.cos(radians))
                layer.rotation = (layer.rotation + angle) % 360
                w, h = layer.display_size
                layer.offset = (round(new_center.x()-w/2), round(new_center.y()-h/2))
        else:
            left, top, right, bottom = r.left(), r.top(), r.right(), r.bottom()
            if "w" in mode: left = min(right-1, left+dx)
            if "e" in mode: right = max(left+1, right+dx)
            if "n" in mode: top = min(bottom-1, top+dy)
            if "s" in mode: bottom = max(top+1, bottom+dy)
            sx, sy = (right-left)/r.width(), (bottom-top)/r.height()
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier or any(l.rotation % 360 for l in g["layers"]):
                sx = sy = max(sx, sy)
            for layer in g["layers"]:
                layer.offset = (round(left+(layer.offset[0]-r.left())*sx), round(top+(layer.offset[1]-r.top())*sy))
                layer.scale_x = max(.001, layer.scale_x*sx)
                layer.scale_y = max(.001, layer.scale_y*sy)
        self.controller.document_changed.emit()
        self.viewport().update()

    def mouseReleaseEvent(self, event):
        if self._pan_origin is not None:
            self._pan_origin = None
            self.setCursor(Qt.CursorShape.OpenHandCursor if self._space else Qt.CursorShape.ArrowCursor)
            return
        if self._crop_mode or self._point_mode:
            return self._tool_release(event)
        if self._marquee is not None:
            rect = self._marquee.normalized()
            ids = self._marquee_ids + [l.id for l in self.controller.document.layers
                                       if l.visible and not l.locked and rect.contains(self.layer_rect(l))]
            self._marquee = None
            self.controller.select(ids)
        if self._gesture:
            from ..core.commands import transform_state, set_transform
            g = self._gesture
            after = {l.id: transform_state(l) for l in g["layers"]}
            for layer in g["layers"]:
                set_transform(layer, g["before"][layer.id])
            self._gesture = None
            self.controller.transform_selection(g["before"], after)
        self._snap_guides = []
        self.viewport().update()

    def cancel_gesture(self):
        if self._gesture:
            from ..core.commands import set_transform
            for layer in self._gesture["layers"]:
                set_transform(layer, self._gesture["before"][layer.id])
            self._gesture = None
            self.controller.document_changed.emit()
        self._marquee = None
        self._snap_guides = []
        self.cancel_crop()
        self.end_point_tool()
        self.viewport().update()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Space:
            self._space = True
            self.setCursor(Qt.CursorShape.OpenHandCursor)
            return
        if event.key() == Qt.Key.Key_Escape:
            self.cancel_gesture()
            return
        directions = {Qt.Key.Key_Left: (-1, 0), Qt.Key.Key_Right: (1, 0),
                      Qt.Key.Key_Up: (0, -1), Qt.Key.Key_Down: (0, 1)}
        if self.controller and not self.read_only and event.key() in directions:
            dx, dy = directions[event.key()]
            amount = 10 if event.modifiers() & Qt.KeyboardModifier.ShiftModifier else 1
            self.controller.nudge_selection(dx*amount, dy*amount)
            return
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key.Key_Space:
            self._space = False
            self.unsetCursor()
            return
        super().keyReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        if self.read_only:
            return
        layer = self._hit_layer(self.mapToScene(event.position().toPoint()))
        if layer and layer.kind.value == "text" and not layer.locked:
            from PySide6.QtWidgets import QInputDialog
            self.controller.select([layer.id])
            text, ok = QInputDialog.getMultiLineText(self, "Edit text", "Text:", layer.spec.get("text", ""))
            if ok:
                self.controller.set_text(text)
        else:
            super().mouseDoubleClickEvent(event)
