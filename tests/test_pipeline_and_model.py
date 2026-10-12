import importlib
import pkgutil

import numpy as np

import photostudio.core as core_pkg
import photostudio.imaging as imaging_pkg
from photostudio.core.document import Document, Layer, BlendMode
from photostudio.core.pipeline import composite


def test_nondestructive_composite_leaves_pixels_untouched():
    img = np.full((8, 8, 4), 100, dtype=np.uint8)
    doc = Document.from_image(img)
    doc.active_layer.adjustments["brightness"] = 0.5
    before = doc.active_layer.pixels.copy()
    out = composite(doc)
    # Adjustment affected output but NOT the stored layer pixels.
    assert out[..., :3].mean() > 100
    assert np.array_equal(doc.active_layer.pixels, before)


def test_hidden_layer_not_composited():
    base = np.zeros((4, 4, 4), dtype=np.uint8)
    base[..., 3] = 255
    top = np.full((4, 4, 4), 255, dtype=np.uint8)
    doc = Document(width=4, height=4, layers=[
        Layer(pixels=base, name="base"),
        Layer(pixels=top, name="top", visible=False),
    ])
    out = composite(doc)
    assert out[..., :3].max() == 0  # top hidden, base is black


def test_layer_validation_rejects_bad_shape():
    import pytest
    with pytest.raises(ValueError):
        Layer(pixels=np.zeros((4, 4, 3), dtype=np.uint8))


def test_core_and_imaging_have_no_qt_imports():
    """Architecture guard: core/imaging must not import PySide6."""
    for pkg in (core_pkg, imaging_pkg):
        for mod in pkgutil.iter_modules(pkg.__path__):
            module = importlib.import_module(f"{pkg.__name__}.{mod.name}")
            src = module.__file__
            with open(src, encoding="utf-8") as fh:
                text = fh.read()
            # The real architectural boundary: no Qt/UI imports in core or imaging.
            assert "PySide6" not in text, f"{src} imports PySide6"
            assert "from ..ui" not in text and "import ui" not in text, \
                f"{src} imports the UI layer"
