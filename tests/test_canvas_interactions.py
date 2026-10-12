import numpy as np
import pytest
from PySide6.QtCore import QPointF, Qt
from PySide6.QtTest import QTest
from photostudio.core.document import Document
from photostudio.core.pipeline import composite
from photostudio.core import project_io
from photostudio.ui.canvas import CanvasView
from photostudio.ui.controller import EditorController


@pytest.fixture
def editor(qtbot):
    c = EditorController()
    c.new_document(400, 300)
    c.document.layers[0].locked = True
    a = Document.make_shape_layer("rectangle", width=60, height=40)
    a.offset = (80, 80)
    b = Document.make_shape_layer("ellipse", width=50, height=50)
    b.offset = (250, 180)
    c.document.add_layer(a)
    c.document.add_layer(b)
    c.select([])
    view = CanvasView()
    qtbot.addWidget(view)
    view.resize(800, 600)
    view.bind_controller(c)
    view.set_image(c.render())
    view.set_zoom(1)
    view.show()
    view.snap_enabled = False
    return c, view, a, b


def drag(view, start, end):
    p0, p1 = view.mapFromScene(QPointF(*start)), view.mapFromScene(QPointF(*end))
    QTest.mousePress(view.viewport(), Qt.MouseButton.LeftButton, pos=p0)
    QTest.mouseMove(view.viewport(), p1)
    QTest.mouseRelease(view.viewport(), Qt.MouseButton.LeftButton, pos=p1)


@pytest.mark.parametrize("zoom", [.5, 1, 2])
def test_mouse_drag_at_zoom_and_undo(editor, zoom):
    c, view, a, b = editor
    view.set_zoom(zoom)
    drag(view, (100, 100), (130, 120))
    assert a.offset == (110, 100)
    assert c.selected_ids == [a.id]
    c.undo()
    assert a.offset == (80, 80)
    assert not c.can_undo
    c.redo()
    assert a.offset == (110, 100)


def test_resize_handles_rotation_and_persistence(editor, tmp_path):
    c, view, a, b = editor
    c.select([a.id])
    drag(view, (140, 120), (170, 140))
    assert a.scale_x == a.scale_y == 1.5
    assert a.pixels is None
    c.undo()
    assert a.scale_x == 1
    # Handle above top edge rotates around centre (110,100).
    drag(view, (110, 52), (158, 100))
    assert a.rotation == pytest.approx(90)
    assert a.display_size == (40, 60)
    assert a.render().shape[:2] == (60, 40)
    path = tmp_path / "transform.pstudio"
    project_io.save_project(c.document, path)
    loaded = project_io.load_project(path)
    assert loaded.layer_by_id(a.id).rotation == pytest.approx(90)
    assert np.array_equal(composite(loaded), composite(c.document))
    c.undo()
    assert a.rotation == 0 and a.offset == (80, 80)


def test_shift_select_move_and_keyboard(editor):
    c, view, a, b = editor
    QTest.mouseClick(view.viewport(), Qt.MouseButton.LeftButton, pos=view.mapFromScene(QPointF(100, 100)))
    QTest.mouseClick(view.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.ShiftModifier,
                     pos=view.mapFromScene(QPointF(270, 200)))
    assert set(c.selected_ids) == {a.id, b.id}
    drag(view, (100, 100), (120, 110))
    assert a.offset == (100, 90) and b.offset == (270, 190)
    QTest.keyClick(view, Qt.Key.Key_Right, Qt.KeyboardModifier.ShiftModifier)
    assert a.offset == (110, 90) and b.offset == (280, 190)
    c.undo()
    assert a.offset == (100, 90)
    c.undo()
    assert a.offset == (80, 80) and b.offset == (250, 180)


def test_marquee_and_locked_layer(editor):
    c, view, a, b = editor
    drag(view, (60, 60), (320, 250))
    assert set(c.selected_ids) == {a.id, b.id}
    a.locked = True
    c.select([a.id])
    drag(view, (100, 100), (140, 150))
    assert a.offset == (80, 80)
    c.delete_selection()
    assert c.document.layer_by_id(a.id) is a


def test_snap_and_cancel(editor):
    c, view, a, b = editor
    c.select([a.id])
    view.snap_enabled = True
    drag(view, (100, 100), (22, 100))
    assert a.offset[0] == 0
    c.undo()
    p0 = view.mapFromScene(QPointF(100, 100))
    p1 = view.mapFromScene(QPointF(140, 150))
    QTest.mousePress(view.viewport(), Qt.MouseButton.LeftButton, pos=p0)
    QTest.mouseMove(view.viewport(), p1)
    QTest.keyClick(view, Qt.Key.Key_Escape)
    QTest.mouseRelease(view.viewport(), Qt.MouseButton.LeftButton, pos=p1)
    assert a.offset == (80, 80)
    assert not c.can_undo


def test_duplicate_and_delete_selection_undo(editor):
    c, view, a, b = editor
    c.select([a.id, b.id])
    c.duplicate_selection()
    assert len(c.document.layers) == 5
    assert len(c.selected_ids) == 2
    c.delete_selection()
    assert len(c.document.layers) == 3
    c.undo()
    assert len(c.document.layers) == 5
    c.undo()
    assert len(c.document.layers) == 3
