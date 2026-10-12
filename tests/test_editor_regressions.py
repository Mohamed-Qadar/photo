"""UI regressions for the six confirmed baseline defects."""
import threading
import numpy as np
import pytest
from PySide6.QtCore import QPointF, Qt, QThread
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QMessageBox
from photostudio.ui.canvas import CanvasView
from photostudio.ui.controller import EditorController
from photostudio.ui.main_window import MainWindow
from photostudio.ui.workers import RenderQueue
from photostudio.core.document import Document


def test_crop_mouse_gesture(qtbot):
    canvas = CanvasView()
    qtbot.addWidget(canvas)
    canvas.resize(600, 400)
    canvas.show()
    canvas.set_image(np.full((200, 300, 4), 255, np.uint8))
    canvas.set_zoom(1)
    canvas.begin_crop()
    start = canvas.mapFromScene(QPointF(20, 30))
    end = canvas.mapFromScene(QPointF(120, 100))
    results = []
    canvas.crop_committed.connect(lambda *values: results.append(values))
    QTest.mousePress(canvas.viewport(), Qt.MouseButton.LeftButton, pos=start)
    QTest.mouseMove(canvas.viewport(), end)
    QTest.mouseRelease(canvas.viewport(), Qt.MouseButton.LeftButton, pos=end)
    assert results == [(20, 30, 100, 70)]


@pytest.mark.parametrize("operation", [
    lambda c: c.crop(0, 0, 10, 10), lambda c: c.resize(10, 10),
    lambda c: c.rotate_90(), lambda c: c.flip(True),
    lambda c: c.move_active_layer(20, 20), lambda c: c.set_opacity(.2),
    lambda c: c.delete_active_layer(), lambda c: c.apply_filter("Sharpen"),
    lambda c: c.apply_beauty("Skin Smoothing"), lambda c: c.heal_at(5, 5),
    lambda c: c.replace_background(), lambda c: c.set_adjustment("brightness", .4),
])
def test_locked_layer_cannot_be_edited(qapp, operation):
    c = EditorController()
    c.new_document(30, 20)
    layer = c.document.active_layer
    layer.locked = True
    original = layer.pixels.copy()
    operation(c)
    assert len(c.document.layers) == 1
    assert layer.offset == (0, 0) and layer.opacity == 1
    assert np.array_equal(layer.pixels, original)
    assert not c.can_undo


def test_cancel_close_and_cancel_save_keep_document(qtbot, monkeypatch):
    win = MainWindow()
    qtbot.addWidget(win)
    win.controller.new_document(100, 80)
    win.controller.add_text("Keep me")
    monkeypatch.setattr(QMessageBox, "warning", lambda *a: QMessageBox.StandardButton.Cancel)
    assert not win._confirm_replace()
    monkeypatch.setattr(QMessageBox, "warning", lambda *a: QMessageBox.StandardButton.Save)
    monkeypatch.setattr(win, "on_save", lambda: None)
    assert not win._confirm_replace()
    win.controller._dirty = False


def test_text_controls_edit_and_undo(qtbot):
    win = MainWindow()
    qtbot.addWidget(win)
    win.controller.new_document(200, 100)
    win.controller.add_text("Salaan")
    panel = win.adjust_panel
    panel.text_input.setText("Soo dhawoow")
    panel.text_input.editingFinished.emit()
    assert win.controller.document.active_layer.spec["text"] == "Soo dhawoow"
    win.controller.undo()
    assert win.controller.document.active_layer.spec["text"] == "Salaan"
    win.controller._dirty = False
    win.render_queue.pool.waitForDone()


def test_worker_snapshot_and_latest_result(qtbot, monkeypatch):
    import photostudio.ui.workers as workers
    started = threading.Event()
    release = threading.Event()
    threads = []
    original = workers.composite
    def render(doc, **kwargs):
        threads.append(QThread.currentThread())
        if len(threads) == 1:
            started.set()
            release.wait(3)
        return original(doc, **kwargs)
    monkeypatch.setattr(workers, "composite", render)
    queue = RenderQueue()
    doc = Document.blank(10, 10)
    results = []
    delivery_threads = []
    queue.ready.connect(lambda px: (results.append(px), delivery_threads.append(QThread.currentThread())))
    queue.request(doc)
    qtbot.waitUntil(started.is_set)
    doc.layers[0].opacity = 0
    queue.request(doc)
    release.set()
    qtbot.waitUntil(lambda: len(results) == 1)
    assert results[0][..., 3].max() == 0
    assert all(thread != queue.thread() for thread in threads)
    assert delivery_threads == [queue.thread()]
    queue.pool.waitForDone()
