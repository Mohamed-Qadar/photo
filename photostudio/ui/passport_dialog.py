"""Physical layout settings; examples are not official biometric requirements."""
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLabel,
    QComboBox, QDoubleSpinBox, QSpinBox, QDialogButtonBox)
from ..core.passport import PHOTO_SIZES, SHEET_SIZES, sheet_capacity


class PassportDialog(QDialog):
    def __init__(self, sheet_key, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Passport print layout")
        layout = QVBoxLayout(self)
        notice = QLabel("Example sizes only. Verify the dimensions, background and composition with the issuing authority.")
        notice.setWordWrap(True)
        layout.addWidget(notice)
        form = QFormLayout()
        layout.addLayout(form)
        self.presets = QComboBox()
        self.presets.addItems([p.label for p in PHOTO_SIZES] + ["Custom size"])
        form.addRow("Photo size", self.presets)
        self.width_mm, self.height_mm = QDoubleSpinBox(), QDoubleSpinBox()
        for widget in (self.width_mm, self.height_mm):
            widget.setRange(5, 300)
            widget.setSuffix(" mm")
        form.addRow("Width", self.width_mm)
        form.addRow("Height", self.height_mm)
        self.dpi = QSpinBox()
        self.dpi.setRange(72, 600)
        self.dpi.setValue(300)
        form.addRow("DPI", self.dpi)
        self.copies = QSpinBox()
        self.copies.setRange(1, 100)
        form.addRow("Copies", self.copies)
        self.capacity = QLabel()
        layout.addWidget(self.capacity)
        self.sheet = next(s for s in SHEET_SIZES if s.key == sheet_key)
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)
        self.presets.currentIndexChanged.connect(self._preset)
        for widget in (self.width_mm, self.height_mm, self.dpi):
            widget.valueChanged.connect(self._capacity)
        self._preset(0)

    def _preset(self, index):
        if index < len(PHOTO_SIZES):
            size = PHOTO_SIZES[index]
            self.width_mm.setValue(size.width_mm)
            self.height_mm.setValue(size.height_mm)
        self._capacity()

    def _capacity(self):
        cols, rows = sheet_capacity(self.width_mm.value(), self.height_mm.value(), self.sheet, self.dpi.value())
        count = cols*rows
        self.copies.setMaximum(max(1, count))
        self.capacity.setText(f"Sheet capacity: {count} photos ({cols} × {rows})")
        self.buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(count > 0)

    def values(self):
        return self.width_mm.value(), self.height_mm.value(), self.dpi.value(), self.copies.value()
