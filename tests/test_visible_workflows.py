"""Exercise user-facing actions; file chooser selections are supplied by fixtures."""
from PIL import Image
import numpy as np
from PySide6.QtWidgets import QFileDialog, QInputDialog, QMessageBox
from photostudio.ui.main_window import MainWindow
from photostudio.core import project_io
from photostudio.core.document import Document


def test_visible_photo_text_save_reopen_export(qtbot, monkeypatch, tmp_path):
    source = tmp_path / "photo.png"
    Image.new("RGBA", (320, 240), (100, 120, 140, 255)).save(source)
    win = MainWindow()
    qtbot.addWidget(win)
    win.show()
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *a, **k: (str(source), ""))
    win.on_open_image()
    assert win.controller.document.width == 320
    monkeypatch.setattr(QInputDialog, "getText", lambda *a, **k: ("Soo dhawoow", True))
    next(action for action in win.tools.actions() if action.text() == "Text").trigger()
    assert win.controller.document.active_layer.spec["text"] == "Soo dhawoow"
    project = tmp_path / "photo.pstudio"
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *a, **k: (str(project), ""))
    assert win.on_save() is True
    assert not win.controller.is_dirty
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *a, **k: (str(project), ""))
    win.on_open_project()
    assert win.controller.document.layers[-1].spec["text"] == "Soo dhawoow"
    output = tmp_path / "photo.jpg"
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *a, **k: (str(output), "JPEG Image (*.jpg)"))
    win.act_export.trigger()
    with Image.open(output) as image:
        assert image.size == (320, 240) and image.mode == "RGB"
    win.close()


def test_actual_cancelled_save_prevents_close(qtbot, monkeypatch):
    win = MainWindow()
    qtbot.addWidget(win)
    win.show()
    win.controller.new_document(100, 100)
    win.controller.add_text("Keep this")
    monkeypatch.setattr(QMessageBox, "warning", lambda *a: QMessageBox.StandardButton.Save)
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *a, **k: ("", ""))
    assert win.close() is False
    assert win.controller.is_dirty
    assert win.controller.document.layers[-1].spec["text"] == "Keep this"
    win.controller._dirty = False
    win.close()


def test_text_pixels_are_vertically_centered():
    layer = Document.make_text_layer("IIBKA WEYN", width=900, height=140, font_size=110, bold=True)
    alpha = layer.render()[..., 3]
    rows = np.flatnonzero(np.any(alpha > 0, axis=1))
    assert abs((rows[0]+rows[-1])/2 - 70) < 2
