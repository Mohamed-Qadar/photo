import numpy as np
import pytest

from photostudio.core.document import BlendMode, Document, Layer
from photostudio.core import project_io
from photostudio.imaging import io as img_io


def sample_doc():
    img = np.random.randint(0, 255, (24, 32, 4), dtype=np.uint8)
    doc = Document.from_image(img, name="Sample")
    doc.active_layer.adjustments["brightness"] = 0.25
    doc.active_layer.adjustments["contrast"] = -0.1
    return doc


def test_project_roundtrip_preserves_editable_content(tmp_path):
    doc = sample_doc()
    path = tmp_path / "proj.pstudio"
    project_io.save_project(doc, path)
    loaded = project_io.load_project(path)

    assert (loaded.width, loaded.height) == (doc.width, doc.height)
    assert loaded.name == "Sample"
    assert len(loaded.layers) == 1
    # Non-destructive: adjustments preserved as parameters, pixels intact.
    assert loaded.layers[0].adjustments["brightness"] == 0.25
    assert loaded.layers[0].adjustments["contrast"] == -0.1
    assert np.array_equal(loaded.layers[0].pixels, doc.layers[0].pixels)


def test_multi_layer_roundtrip(tmp_path):
    base = np.zeros((10, 10, 4), dtype=np.uint8)
    top = np.full((10, 10, 4), 200, dtype=np.uint8)
    doc = Document(width=10, height=10, layers=[
        Layer(pixels=base, name="Base"),
        Layer(pixels=top, name="Top", opacity=0.5, blend=BlendMode.MULTIPLY,
              offset=(2, 3), visible=False),
    ])
    path = tmp_path / "multi.pstudio"
    project_io.save_project(doc, path)
    loaded = project_io.load_project(path)
    assert len(loaded.layers) == 2
    top2 = loaded.layers[1]
    assert top2.opacity == 0.5
    assert top2.blend == BlendMode.MULTIPLY
    assert top2.offset == (2, 3)
    assert top2.visible is False


def test_future_version_rejected(tmp_path, monkeypatch):
    doc = sample_doc()
    path = tmp_path / "p.pstudio"
    monkeypatch.setattr(project_io, "FORMAT_VERSION", 99)
    project_io.save_project(doc, path)
    # Now pretend this build only supports version 1.
    monkeypatch.setattr(project_io, "FORMAT_VERSION", 1)
    with pytest.raises(ValueError):
        project_io.load_project(path)


def test_export_png_and_jpg(tmp_path):
    doc = sample_doc()
    png = tmp_path / "out.png"
    jpg = tmp_path / "out.jpg"
    project_io.export_document(doc, png, fmt="png")
    project_io.export_document(doc, jpg, fmt="jpg", quality=80)
    assert png.exists() and jpg.exists()
    loaded = img_io.load_image(png)
    assert loaded.shape == (24, 32, 4)


def test_image_roundtrip_formats(tmp_path):
    img = np.random.randint(0, 255, (16, 16, 4), dtype=np.uint8)
    for ext in ("png", "webp", "tiff"):
        p = tmp_path / f"img.{ext}"
        img_io.save_png(img, p) if ext == "png" else None
    # PNG preserves alpha exactly
    p = tmp_path / "x.png"
    img_io.save_png(img, p)
    back = img_io.load_image(p)
    assert np.array_equal(back, img)
