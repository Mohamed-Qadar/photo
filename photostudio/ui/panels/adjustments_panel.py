"""Adjustments (Properties) panel: tone/color sliders.

Slider drags coalesce into one undo step (AdjustmentCommand.merge_with).
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QPushButton, QSlider,
                               QVBoxLayout, QWidget)

from ..controller import EditorController

# (key, title, min, max) — slider integer range; value = slider/100.
ROWS = [
    ("exposure", "Exposure", -100, 100),
    ("brightness", "Brightness", -100, 100),
    ("contrast", "Contrast", -100, 100),
    ("saturation", "Saturation", -100, 100),
    ("temperature", "Temperature", -100, 100),
    ("grayscale", "Grayscale", 0, 100),
]


class _SliderRow(QWidget):
    def __init__(self, title: str, key: str, lo: int, hi: int,
                 controller: EditorController):
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
        self.slider.setRange(lo, hi)
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

        self.rows = {}
        for key, label, lo, hi in ROWS:
            row = _SliderRow(label, key, lo, hi, controller)
            self.rows[key] = row
            layout.addWidget(row)

        self.reset_btn = QPushButton("Reset adjustments")
        self.reset_btn.clicked.connect(self._reset)
        layout.addWidget(self.reset_btn)
        layout.addStretch(1)

        controller.document_opened.connect(self.refresh)
        controller.document_changed.connect(self.refresh)

    def _reset(self):
        for key in self.rows:
            self.controller.set_adjustment(key, 0.0)
        self.refresh()

    def refresh(self):
        layer = self.controller.document.active_layer if self.controller.document else None
        enabled = layer is not None
        self.setEnabled(enabled)
        if layer is not None:
            for key, row in self.rows.items():
                row.sync(layer.adjustments.get(key, 0.0))
