"""Milestone D: alignment, snapping, layer management, grouping, typography."""
import numpy as np

from photostudio.core.document import Document
from photostudio.core.history import History
from photostudio.core import commands, project_io
from photostudio.core.arrange import align_offset, snap, snap_offset


def _doc():
    return Document.blank(400, 300)


def test_align_offsets():
    assert align_offset(100, 50, 400, 300, "left", (33, 33)) == (0, 33)
    assert align_offset(100, 50, 400, 300, "right", (0, 10)) == (300, 10)
    assert align_offset(100, 50, 400, 300, "hcenter", (0, 7)) == (150, 7)
    assert align_offset(100, 50, 400, 300, "vcenter", (5, 0)) == (5, 125)
    assert align_offset(100, 50, 400, 300, "bottom", (5, 0)) == (5, 250)


def test_snap_to_target():
    assert snap(5, [0, 150, 300], 12) == 0        # within threshold
    assert snap(40, [0, 150, 300], 12) == 40      # no target close
    assert snap_offset((6, 130), 100, 50, 400, 300) == (0, 125)  # 130 within 12 of 125


def test_align_command_center():
    doc = _doc()
    sh = Document.make_shape_layer("rectangle", width=100, height=50)
    doc.add_layer(sh)
    hist = History()
    hist.push(commands.AlignCommand(doc, sh, "hcenter"))
    assert sh.offset[0] == 150
    hist.undo()
    assert sh.offset == (0, 0)


def test_reorder_duplicate_opacity():
    doc = _doc()
    a = Document.make_shape_layer("rectangle", width=20, height=20, name="A")
    b = Document.make_shape_layer("ellipse", width=20, height=20, name="B")
    doc.add_layer(a); doc.add_layer(b)
    hist = History()
    # b is on top (last). Lower it.
    hist.push(commands.ReorderLayerCommand(doc, b, -1))
    assert doc.index_of(b.id) < doc.index_of(a.id)
    hist.undo()
    assert doc.index_of(b.id) > doc.index_of(a.id)
    # duplicate
    n0 = len(doc.layers)
    hist.push(commands.DuplicateLayerCommand(doc, a))
    assert len(doc.layers) == n0 + 1
    # opacity coalesces
    for o in (0.8, 0.6, 0.4):
        hist.push(commands.SetOpacityCommand(a, o))
    assert a.opacity == 0.4
    hist.undo()
    assert a.opacity == 1.0


def test_grouping_and_group_move():
    doc = _doc()
    a = Document.make_shape_layer("rectangle", width=20, height=20)
    b = Document.make_shape_layer("ellipse", width=20, height=20)
    doc.add_layer(a); doc.add_layer(b)
    hist = History()
    hist.push(commands.GroupCommand([a, b], "g1"))
    assert a.group == b.group == "g1"
    hist.push(commands.MoveGroupCommand([a, b], 10, 5))
    assert a.offset == (10, 5) and b.offset == (10, 5)
    hist.undo()
    assert a.offset == (0, 0) and b.offset == (0, 0)
    hist.push(commands.GroupCommand([a, b], None))
    assert a.group is None and b.group is None


def test_text_property_command():
    layer = Document.make_text_layer("Hi", width=100, height=40, font_size=20)
    hist = History()
    hist.push(commands.SetTextPropertyCommand(layer, "font_size", 60))
    assert layer.spec["font_size"] == 60
    assert layer.render().shape == (40, 100, 4)
    hist.undo()
    assert layer.spec["font_size"] == 20


def test_group_persists(tmp_path):
    doc = _doc()
    a = Document.make_shape_layer("rectangle", width=20, height=20)
    b = Document.make_shape_layer("ellipse", width=20, height=20)
    a.group = b.group = "grp"
    doc.add_layer(a); doc.add_layer(b)
    p = tmp_path / "g.pstudio"
    project_io.save_project(doc, p)
    loaded = project_io.load_project(p)
    groups = [l.group for l in loaded.layers if l.group]
    assert groups.count("grp") == 2
