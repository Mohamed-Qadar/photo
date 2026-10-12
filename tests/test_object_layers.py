"""Shared-engine tests: text & shape object layers, rendering, persistence, commands."""
import numpy as np

from photostudio.core.document import Document, Layer, LayerKind
from photostudio.core.history import History
from photostudio.core import commands, project_io
from photostudio.core.pipeline import composite


def test_blank_document_has_background():
    doc = Document.blank(200, 120, background=(255, 255, 255, 255))
    assert (doc.width, doc.height) == (200, 120)
    assert len(doc.layers) == 1
    assert doc.layers[0].pixels is not None


def test_text_layer_renders_nontransparent_pixels():
    layer = Document.make_text_layer("Hello", width=200, height=80, font_size=40)
    px = layer.render()
    assert px.shape == (80, 200, 4)
    assert px[..., 3].max() > 0  # some text pixels are opaque


def test_shape_layer_renders_fill():
    layer = Document.make_shape_layer("ellipse", width=60, height=60,
                                      fill=(255, 0, 0, 255))
    px = layer.render()
    assert px.shape == (60, 60, 4)
    # Center pixel should be red and opaque.
    assert tuple(px[30, 30]) == (255, 0, 0, 255)


def test_object_layer_requires_spec():
    import pytest
    with pytest.raises(ValueError):
        Layer(kind=LayerKind.TEXT, spec={})


def test_composite_includes_object_layer():
    doc = Document.blank(100, 100, background=(255, 255, 255, 255))
    shape = Document.make_shape_layer("rectangle", width=40, height=40,
                                      fill=(0, 0, 255, 255))
    shape.offset = (30, 30)
    doc.add_layer(shape)
    out = composite(doc)
    assert tuple(out[50, 50][:3]) == (0, 0, 255)   # shape on top
    assert tuple(out[5, 5][:3]) == (255, 255, 255)  # background elsewhere


def test_object_layers_roundtrip_editable(tmp_path):
    doc = Document.blank(150, 100)
    txt = Document.make_text_layer("Somali Shop", width=150, height=40, font_size=28)
    txt.offset = (0, 30)
    doc.add_layer(txt)
    doc.add_layer(Document.make_shape_layer("rounded", width=80, height=30))
    path = tmp_path / "design.pstudio"
    project_io.save_project(doc, path)
    loaded = project_io.load_project(path)

    assert len(loaded.layers) == 3
    tl = [l for l in loaded.layers if l.kind == LayerKind.TEXT][0]
    assert tl.spec["text"] == "Somali Shop"      # still editable
    assert tl.pixels is None                       # not flattened
    assert tl.render().shape == (40, 150, 4)       # re-renders from spec


def test_add_and_remove_layer_commands_undo():
    doc = Document.blank(100, 100)
    hist = History()
    shape = Document.make_shape_layer("rectangle", width=20, height=20)
    hist.push(commands.AddLayerCommand(doc, shape))
    assert len(doc.layers) == 2
    hist.undo()
    assert len(doc.layers) == 1
    hist.redo()
    assert len(doc.layers) == 2


def test_move_layer_coalesces():
    doc = Document.blank(100, 100)
    shape = Document.make_shape_layer("rectangle", width=20, height=20)
    doc.add_layer(shape)
    hist = History()
    for off in [(5, 5), (10, 10), (15, 15)]:
        hist.push(commands.MoveLayerCommand(shape, off))
    assert shape.offset == (15, 15)
    hist.undo()
    assert shape.offset == (0, 0)  # single coalesced step


def test_text_edit_command():
    layer = Document.make_text_layer("a", width=100, height=30)
    doc = Document.blank(100, 100)
    doc.add_layer(layer)
    hist = History()
    hist.push(commands.SetTextCommand(layer, "hello"))
    assert layer.spec["text"] == "hello"
    hist.undo()
    assert layer.spec["text"] == "a"
