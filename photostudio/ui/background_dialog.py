"""Beginner-friendly solid / gradient canvas background controls."""
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QDialog,QVBoxLayout,QHBoxLayout,QComboBox,QPushButton,
                               QColorDialog,QSpinBox,QLabel)
from .i18n import tr


class BackgroundDialog(QDialog):
    def __init__(self,layer,parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("Canvas background"))
        self.resize(420,260)
        spec = layer.spec if layer else {}
        gradient = spec.get("gradient")
        first = spec.get("fill") or ([int(v) for v in layer.pixels[0,0]] if layer and layer.pixels is not None else [255]*4)
        self.colors = [QColor(*first),QColor(35,90,180)]
        if gradient:
            self.colors = [QColor(*gradient["stops"][0][1]),QColor(*gradient["stops"][-1][1])]
        layout = QVBoxLayout(self)
        self.mode = QComboBox()
        self.mode.addItems([tr("Solid color"),tr("Gradient")])
        self.mode.setCurrentIndex(1 if gradient else 0)
        layout.addWidget(self.mode)
        self.color_buttons = []
        for i,label in enumerate(("Start color…","End color…")):
            button = QPushButton(tr(label))
            button.setMinimumHeight(36)
            button.clicked.connect(lambda checked=False,index=i: self.choose(index))
            self.color_buttons.append(button)
            layout.addWidget(button)
        self.angle = QSpinBox()
        self.angle.setRange(0,360)
        self.angle.setPrefix(tr("Gradient angle: "))
        self.angle.setValue(int(gradient.get("angle",90)) if gradient else 90)
        layout.addWidget(self.angle)
        self.preview = QLabel()
        self.preview.setMinimumHeight(45)
        layout.addWidget(self.preview)
        row = QHBoxLayout()
        layout.addLayout(row)
        cancel = QPushButton(tr("Cancel"))
        cancel.clicked.connect(self.reject)
        row.addWidget(cancel)
        apply = QPushButton(tr("Apply"))
        apply.setObjectName("primary")
        apply.setMinimumHeight(36)
        apply.clicked.connect(self.accept)
        row.addWidget(apply)
        self.mode.currentIndexChanged.connect(self.refresh)
        self.angle.valueChanged.connect(self.refresh)
        self.refresh()

    def choose(self,index):
        color = QColorDialog.getColor(self.colors[index],self)
        if color.isValid():
            self.colors[index] = color
            self.refresh()

    def refresh(self,*args):
        gradient = self.mode.currentIndex() == 1
        self.color_buttons[1].setEnabled(gradient)
        self.angle.setEnabled(gradient)
        a,b = [c.name() for c in self.colors]
        import math
        angle = math.radians(self.angle.value())
        x,y = math.cos(angle)/2,math.sin(angle)/2
        self.preview.setStyleSheet(f"background: qlineargradient(x1:{.5-x},y1:{.5-y},x2:{.5+x},y2:{.5+y},stop:0 {a},stop:1 {b}); border-radius:6px;" if gradient else f"background:{a};border-radius:6px;")

    def apply_to(self,controller):
        colors = [[c.red(),c.green(),c.blue(),255] for c in self.colors]
        if self.mode.currentIndex() == 1:
            controller.set_canvas_gradient(*colors,self.angle.value())
        else:
            controller.set_canvas_background(colors[0])
