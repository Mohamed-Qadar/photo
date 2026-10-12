"""Adjustments (Properties) panel: tone/color sliders.

Slider drags coalesce into one undo step (AdjustmentCommand.merge_with).
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QPushButton, QSlider,
                               QVBoxLayout, QWidget, QLineEdit, QSpinBox, QComboBox, QColorDialog)

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

        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Edit selected text")
        self.text_input.editingFinished.connect(lambda: controller.set_text(self.text_input.text()))
        layout.addWidget(self.text_input)
        self.font_size = QSpinBox()
        self.font_size.setRange(1, 1000)
        self.font_size.setPrefix("Font size: ")
        self.font_size.valueChanged.connect(lambda v: controller.set_text_property("font_size", v))
        layout.addWidget(self.font_size)
        self.text_align = QComboBox()
        self.text_align.addItems(["left", "center", "right"])
        self.text_align.currentTextChanged.connect(lambda v: controller.set_text_property("align", v))
        layout.addWidget(self.text_align)
        self.text_color = QPushButton("Text colour…")
        self.text_color.clicked.connect(self._text_color)
        layout.addWidget(self.text_color)
        self.snap_btn = QPushButton("Snap selected to canvas")
        self.snap_btn.clicked.connect(self._snap)
        layout.addWidget(self.snap_btn)
        self.reset_btn = QPushButton("Reset adjustments")
        self.reset_btn.clicked.connect(self._reset)
        layout.addWidget(self.reset_btn)
        layout.addStretch(1)

        controller.document_opened.connect(self.refresh)
        controller.document_changed.connect(self.refresh)
        controller.selection_changed.connect(self.refresh)

    def _text_color(self):
        c = QColorDialog.getColor(parent=self)
        if c.isValid():
            self.controller.set_text_property("color", [c.red(), c.green(), c.blue(), c.alpha()])

    def _snap(self):
        from ...core.arrange import snap_offset
        doc = self.controller.document
        layer = self.controller._active()
        if layer:
            self.controller.move_active_layer(*snap_offset(layer.offset, layer.width, layer.height, doc.width, doc.height))

    def _reset(self):
        for key in self.rows:
            self.controller.set_adjustment(key, 0.0)
        self.refresh()

    def refresh(self):
        layer = self.controller.document.active_layer if self.controller.document else None
        enabled = layer is not None and not layer.locked
        self.setEnabled(enabled)
        is_text = layer is not None and layer.kind.value == "text"
        for widget in (self.text_input, self.font_size, self.text_align, self.text_color):
            widget.setVisible(is_text)
        if is_text:
            for widget in (self.text_input, self.font_size, self.text_align):
                widget.blockSignals(True)
            if not self.text_input.hasFocus():
                self.text_input.setText(layer.spec.get("text", ""))
            self.font_size.setValue(layer.spec.get("font_size", 48))
            self.text_align.setCurrentText(layer.spec.get("align", "center"))
            for widget in (self.text_input, self.font_size, self.text_align):
                widget.blockSignals(False)
        if layer is not None:
            for key, row in self.rows.items():
                row.sync(layer.adjustments.get(key, 0.0))
