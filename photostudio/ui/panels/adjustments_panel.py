"""Adjustments (Properties) panel: brightness / contrast sliders.

Slider drags coalesce into one undo step (handled in AdjustmentCommand.merge_with).
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QSlider, QVBoxLayout, QWidget)

from ..controller import EditorController


class _SliderRow(QWidget):
    def __init__(self, title: str, key: str, controller: EditorController):
        super().__init__()
        self.key = key
        self.controller = controller
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        header = QHBoxLayout()
        self.label = QLabel(title)
        self.value_label = QLabel("0")
        self.value_label.setObjectName("muted")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        header.addWidget(self.label)
        header.addWidget(self.value_label)
        layout.addLayout(header)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(-100, 100)
        self.slider.setValue(0)
        self.slider.valueChanged.connect(self._on_change)
        layout.addWidget(self.slider)

    def _on_change(self, value: int):
        self.value_label.setText(str(value))
        self.controller.set_adjustment(self.key, value / 100.0)

    def sync(self, value: float):
        self.slider.blockSignals(True)
        self.slider.setValue(int(round(value * 100)))
        self.value_label.setText(str(int(round(value * 100))))
        self.slider.blockSignals(False)


class AdjustmentsPanel(QWidget):
    def __init__(self, controller: EditorController):
        super().__init__()
        self.controller = controller
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        title = QLabel("Adjustments")
        title.setStyleSheet("font-weight:600;")
        layout.addWidget(title)

        self.rows = {
            "brightness": _SliderRow("Brightness", "brightness", controller),
            "contrast": _SliderRow("Contrast", "contrast", controller),
        }
        for row in self.rows.values():
            layout.addWidget(row)
        layout.addStretch(1)

        controller.document_opened.connect(self.refresh)

    def refresh(self):
        layer = self.controller.document.active_layer if self.controller.document else None
        enabled = layer is not None
        for key, row in self.rows.items():
            row.setEnabled(enabled)
            if layer is not None:
                row.sync(layer.adjustments.get(key, 0.0))
