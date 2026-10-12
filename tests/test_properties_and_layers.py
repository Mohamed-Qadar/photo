import numpy as np
from PySide6.QtTest import QTest
from PySide6.QtCore import Qt
from photostudio.ui.main_window import MainWindow
from photostudio.core.pipeline import composite
from photostudio.core import project_io
from photostudio.imaging.io import load_image


def window(qtbot):
    win = MainWindow()
    qtbot.addWidget(win)
    win.controller.new_document(300, 200)
    win.controller.add_text("Dukaanka Magaalada")
    win.controller.add_shape("ellipse")
    return win


def finish(win):
    win.controller._dirty = False
    win.render_queue.pool.waitForDone()
    win.layers_panel.thumbnails.pool.waitForDone()


def test_layer_selection_rename_visibility_order_and_undo(qtbot):
    win = window(qtbot)
    c, panel = win.controller, win.layers_panel
    ids = [l.id for l in c.document.layers]
    c.select(ids[1:])
    assert set(panel.selected_layer_ids()) == set(ids[1:])
    item = panel.list.item(0)
    item.setText("Blue ellipse")
    assert c.document.layers[-1].name == "Blue ellipse"
    assert c.is_dirty
    c.undo()
    assert panel.list.item(0).text() == "Ellipse"
    panel.list.item(0).setCheckState(Qt.CheckState.Unchecked)
    assert not c.document.layers[-1].visible
    c.undo()
    assert panel.list.item(0).checkState() == Qt.CheckState.Checked
    c.reorder_layers([ids[0], ids[2], ids[1]], [ids[2]])
    assert panel.list.item(0).data(Qt.ItemDataRole.UserRole) == ids[1]
    c.undo()
    assert [l.id for l in c.document.layers] == ids
    qtbot.waitUntil(lambda: not panel.list.item(0).icon().isNull())
    finish(win)


def test_properties_typography_shape_export_and_project(qtbot, tmp_path):
    win = window(qtbot)
    c, p = win.controller, win.adjust_panel
    text = c.document.layers[1]
    c.select([text.id])
    p.bold.setChecked(True)
    p.outline.setValue(2)
    p.shadow.setValue(3)
    p.font_size.setValue(32)
    p.text_align.setCurrentText("left")
    assert text.spec["bold"] and text.spec["outline_width"] == 2
    assert text.spec["shadow_offset"] == 3 and text.spec["align"] == "left"
    p.transforms["x"].setValue(12)
    assert text.offset[0] == 12
    c.undo()
    assert text.offset[0] != 12
    shape = c.document.layers[2]
    c.select([shape.id])
    p.shape_kind.setCurrentText("triangle")
    p.stroke_width.setValue(3)
    assert shape.spec["shape"] == "triangle" and shape.spec["stroke_width"] == 3
    project = tmp_path / "somali.pstudio"
    png = tmp_path / "somali.png"
    c.save_project(project)
    c.export(png, "png")
    loaded = project_io.load_project(project)
    assert loaded.layers[1].spec["text"] == "Dukaanka Magaalada"
    assert np.array_equal(load_image(png), composite(loaded))
    finish(win)


def test_locked_controls_and_reorder_refused(qtbot):
    win = window(qtbot)
    c = win.controller
    layer = c.document.active_layer
    c.set_locked(layer.id, True)
    assert not win.adjust_panel.isEnabled()
    assert not win.layers_panel.opacity.isEnabled()
    old = [l.id for l in c.document.layers]
    c.reorder_layers(list(reversed(old)), [layer.id])
    assert [l.id for l in c.document.layers] == old
    c.rename_layer(layer.id, "Forbidden")
    assert layer.name != "Forbidden"
    c.set_locked(layer.id, False)
    assert win.adjust_panel.isEnabled()
    finish(win)


def test_layer_mouse_drag_reorders_and_undo(qtbot):
    win = window(qtbot)
    win.layers_panel.list.setMinimumHeight(180)
    win.resize(1280, 1000)
    win.show()
    QTest.qWait(20)
    view = win.layers_panel.list
    old = [l.id for l in win.controller.document.layers]
    start = view.visualItemRect(view.item(0)).center()
    target = view.visualItemRect(view.item(1))
    end = target.bottomLeft()
    end.setX(start.x())
    QTest.mousePress(view.viewport(), Qt.MouseButton.LeftButton, pos=start)
    QTest.mouseMove(view.viewport(), end)
    QTest.mouseRelease(view.viewport(), Qt.MouseButton.LeftButton, pos=end)
    assert [l.id for l in win.controller.document.layers] == [old[0], old[2], old[1]]
    win.controller.undo()
    assert [l.id for l in win.controller.document.layers] == old
    finish(win)
