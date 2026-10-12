import numpy as np

from photostudio.core.document import Document
from photostudio.core.history import History
from photostudio.core import commands


def make_doc():
    img = np.full((20, 30, 4), 120, dtype=np.uint8)
    return Document.from_image(img)


def test_undo_redo_adjustment():
    doc = make_doc()
    hist = History()
    layer = doc.active_layer
    hist.push(commands.AdjustmentCommand(layer, "brightness", 0.5))
    assert layer.adjustments["brightness"] == 0.5
    hist.undo()
    assert layer.adjustments["brightness"] == 0.0
    hist.redo()
    assert layer.adjustments["brightness"] == 0.5


def test_adjustment_coalescing_is_single_step():
    doc = make_doc()
    hist = History()
    layer = doc.active_layer
    for v in (0.1, 0.2, 0.3):
        hist.push(commands.AdjustmentCommand(layer, "brightness", v))
    assert layer.adjustments["brightness"] == 0.3
    hist.undo()  # one undo should return to neutral, not 0.2
    assert layer.adjustments["brightness"] == 0.0
    assert not hist.can_undo()


def test_crop_undo_restores_size():
    doc = make_doc()
    hist = History()
    layer = doc.active_layer
    hist.push(commands.CropCommand(doc, layer, 0, 0, 10, 8))
    assert (doc.width, doc.height) == (10, 8)
    hist.undo()
    assert (doc.width, doc.height) == (30, 20)


def test_new_action_clears_redo():
    doc = make_doc()
    hist = History()
    layer = doc.active_layer
    hist.push(commands.Rotate90Command(doc, layer, 1))
    hist.undo()
    assert hist.can_redo()
    hist.push(commands.FlipCommand(doc, layer, True))
    assert not hist.can_redo()
