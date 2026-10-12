"""Adjustments (Properties) panel: tone/color sliders.

Slider drags coalesce into one undo step (AdjustmentCommand.merge_with).
"""
from __future__ import annotations
from ..i18n import tr, source_text

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QPushButton, QSlider,
                               QVBoxLayout, QWidget, QLineEdit, QSpinBox, QComboBox, QColorDialog, QFontComboBox, QCheckBox, QFormLayout, QGroupBox, QDoubleSpinBox)

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
        self.label = QLabel(tr(title))
        self.value_label = QLabel(tr("0"))
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

        title = QLabel(tr("Adjustments"))
        title.setStyleSheet("font-weight:600;")
        layout.addWidget(title)

        self.rows = {}
        for key, label, lo, hi in ROWS:
            row = _SliderRow(label, key, lo, hi, controller)
            self.rows[key] = row
            layout.addWidget(row)

        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText(tr("Edit selected text"))
        self.text_input.editingFinished.connect(lambda: controller.set_text(self.text_input.text()))
        layout.addWidget(self.text_input)
        self.font_size = QSpinBox()
        self.font_size.setRange(1, 1000)
        self.font_size.setPrefix(tr("Font size: "))
        self.font_size.valueChanged.connect(lambda v: controller.set_text_property("font_size", v))
        layout.addWidget(self.font_size)
        self.text_align = QComboBox()
        self.text_align.addItems([tr(item) for item in ["left", "center", "right"]])
        self.text_align.currentTextChanged.connect(lambda v: controller.set_text_property("align", source_text(v)))
        layout.addWidget(self.text_align)
        self.text_color = QPushButton(tr("Text colour…"))
        self.text_color.clicked.connect(self._text_color)
        layout.addWidget(self.text_color)
        self.snap_btn = QPushButton(tr("Snap selected to canvas"))
        self.snap_btn.clicked.connect(self._snap)
        layout.addWidget(self.snap_btn)
        self.font_family = QFontComboBox()
        self.font_family.currentFontChanged.connect(lambda f: controller.set_text_property("font_family", f.family()))
        layout.addWidget(self.font_family)
        self.bold = QCheckBox(tr("Bold"))
        self.bold.toggled.connect(lambda v: controller.set_text_property("bold", v))
        layout.addWidget(self.bold)
        self.outline = QSpinBox()
        self.outline.setRange(0, 40)
        self.outline.setPrefix(tr("Text outline: "))
        self.outline.valueChanged.connect(lambda v: controller.set_text_property("outline_width", v))
        layout.addWidget(self.outline)
        self.shadow = QSpinBox()
        self.shadow.setRange(0, 100)
        self.shadow.setPrefix(tr("Shadow offset: "))
        self.shadow.valueChanged.connect(lambda v: controller.set_text_property("shadow_offset", v))
        layout.addWidget(self.shadow)
        self.shape_group = QGroupBox(tr("Shape"))
        shape_layout = QVBoxLayout(self.shape_group)
        self.shape_kind = QComboBox()
        self.shape_kind.addItems([tr(item) for item in ["rectangle", "rounded", "ellipse", "triangle", "line"]])
        self.shape_kind.currentTextChanged.connect(lambda v: controller.set_object_property("shape", source_text(v)))
        shape_layout.addWidget(self.shape_kind)
        for title, key in [("Fill colour…", "fill"), ("Stroke colour…", "stroke")]:
            button = QPushButton(tr(title))
            button.clicked.connect(lambda _=False, k=key: self._object_color(k))
            shape_layout.addWidget(button)
        self.stroke_width = QSpinBox()
        self.stroke_width.setRange(0, 100)
        self.stroke_width.setPrefix(tr("Stroke: "))
        self.stroke_width.valueChanged.connect(lambda v: controller.set_object_property("stroke_width", v))
        shape_layout.addWidget(self.stroke_width)
        gradient = QPushButton(tr("Gradient fill…"))
        gradient.clicked.connect(self._gradient)
        shape_layout.addWidget(gradient)
        layout.addWidget(self.shape_group)
        transform = QGroupBox(tr("Transform"))
        form = QFormLayout(transform)
        self.transforms = {}
        for key, title in [("x", "X"), ("y", "Y"), ("width", "Width"), ("height", "Height"), ("rotation", "Rotation")]:
            control = QDoubleSpinBox()
            control.setDecimals(1 if key == "rotation" else 0)
            control.setRange(-100000 if key in ("x", "y", "rotation") else 1, 100000)
            control.setKeyboardTracking(False)
            control.valueChanged.connect(lambda v, k=key: controller.set_transform_property(k, v))
            self.transforms[key] = control
            form.addRow(tr(title), control)
        layout.addWidget(transform)
        layout.addWidget(QLabel(tr("Align to canvas")))
        align_row = QHBoxLayout()
        for title, where in [("←", "left"), ("↔", "hcenter"), ("→", "right"), ("↑", "top"), ("↕", "vcenter"), ("↓", "bottom")]:
            button = QPushButton(tr(title))
            button.setToolTip(tr("Align " + where))
            button.clicked.connect(lambda _=False, w=where: controller.align_active(w))
            align_row.addWidget(button)
        layout.addLayout(align_row)
        beauty = QGroupBox(tr("Portrait tools"))
        beauty_layout = QVBoxLayout(beauty)
        self.beauty_strength = QSlider(Qt.Orientation.Horizontal)
        self.beauty_strength.setRange(0, 100)
        self.beauty_strength.setValue(50)
        self.beauty_strength.setToolTip(tr("Effect strength; preserves facial geometry"))
        beauty_layout.addWidget(self.beauty_strength)
        for name in ("Skin Smoothing", "Portrait Enhance", "Background Blur"):
            button = QPushButton(tr(name))
            button.setToolTip(tr("Approximate blur for centred portraits" if name == "Background Blur" else name))
            button.clicked.connect(lambda _=False, n=name: controller.apply_beauty(n, self.beauty_strength.value()/100))
            beauty_layout.addWidget(button)
        self.heal_radius = QSpinBox()
        self.heal_radius.setRange(2, 100)
        self.heal_radius.setValue(14)
        self.heal_radius.setPrefix(tr("Spot radius: "))
        beauty_layout.addWidget(self.heal_radius)
        layout.addWidget(beauty)
        self.reset_btn = QPushButton(tr("Reset adjustments"))
        self.reset_btn.clicked.connect(self._reset)
        layout.addWidget(self.reset_btn)
        layout.addStretch(1)

        controller.document_opened.connect(self.refresh)
        controller.document_changed.connect(self.refresh)
        controller.selection_changed.connect(self.refresh)

    def _object_color(self, key):
        c = QColorDialog.getColor(parent=self)
        if c.isValid():
            self.controller.set_object_property(key, [c.red(), c.green(), c.blue(), c.alpha()])

    def _gradient(self):
        a = QColorDialog.getColor(parent=self, title="Gradient start")
        if not a.isValid(): return
        b = QColorDialog.getColor(parent=self, title="Gradient end")
        if not b.isValid(): return
        self.controller.set_object_property("gradient", {"angle": 90, "stops": [
            [0, [a.red(), a.green(), a.blue(), 255]], [1, [b.red(), b.green(), b.blue(), 255]]]})

    def _text_color(self):
        c = QColorDialog.getColor(parent=self)
        if c.isValid():
            self.controller.set_text_property("color", [c.red(), c.green(), c.blue(), c.alpha()])

    def _snap(self):
        from ...core.arrange import snap_offset
        doc = self.controller.document
        layer = self.controller._active()
        if layer:
            self.controller.move_active_layer(*snap_offset(layer.offset, *layer.display_size, doc.width, doc.height))

    def _reset(self):
        for key in self.rows:
            self.controller.set_adjustment(key, 0.0)
        self.refresh()

    def refresh(self):
        layer = self.controller.document.active_layer if self.controller.document else None
        enabled = layer is not None and not layer.locked
        self.setEnabled(enabled)
        is_text = layer is not None and layer.kind.value == "text"
        for widget in (self.text_input, self.font_size, self.text_align, self.text_color, self.font_family, self.bold, self.outline, self.shadow):
            widget.setVisible(is_text)
        if is_text:
            for widget in (self.text_input, self.font_size, self.text_align):
                widget.blockSignals(True)
            if not self.text_input.hasFocus():
                self.text_input.setText(layer.spec.get("text", ""))
            self.font_size.setValue(layer.spec.get("font_size", 48))
            self.text_align.setCurrentText(tr(layer.spec.get("align", "center")))
            for widget in (self.text_input, self.font_size, self.text_align):
                widget.blockSignals(False)
        if layer is not None:
            for key, control in self.transforms.items():
                control.blockSignals(True)
                value = {"x": layer.offset[0], "y": layer.offset[1], "width": layer.width*layer.scale_x,
                         "height": layer.height*layer.scale_y, "rotation": layer.rotation}[key]
                control.setValue(value)
                control.blockSignals(False)
            for widget in (self.font_family, self.bold, self.outline, self.shadow, self.shape_kind, self.stroke_width):
                widget.blockSignals(True)
            if is_text:
                from PySide6.QtGui import QFont
                self.font_family.setCurrentFont(QFont(layer.spec.get("font_family", "Segoe UI")))
                self.bold.setChecked(layer.spec.get("bold", False))
                self.outline.setValue(layer.spec.get("outline_width", 0))
                self.shadow.setValue(layer.spec.get("shadow_offset", 0))
            self.shape_group.setVisible(layer.kind.value == "shape")
            if layer.kind.value == "shape":
                self.shape_kind.setCurrentText(tr(layer.spec.get("shape", "rectangle")))
                self.stroke_width.setValue(layer.spec.get("stroke_width", 0))
            for widget in (self.font_family, self.bold, self.outline, self.shadow, self.shape_kind, self.stroke_width):
                widget.blockSignals(False)
            for key, row in self.rows.items():
                row.sync(layer.adjustments.get(key, 0.0))
