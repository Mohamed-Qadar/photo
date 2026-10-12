import numpy as np
import pytest
import threading
from photostudio.core.document import Document
from photostudio.core import passport
from photostudio.ui.controller import EditorController
from photostudio.ui.passport_dialog import PassportDialog


def test_before_session_includes_beauty_and_geometry(qapp):
    c = EditorController()
    image = np.full((80, 60, 4), 100, np.uint8)
    image[..., 3] = 255
    c._attach(Document.from_image(image))
    c.apply_beauty("Portrait Enhance", .8)
    assert np.array_equal(c.render(False), image)
    assert c.render(True)[..., :3].mean() > image[..., :3].mean()
    c.crop(0, 0, 30, 40)
    assert c.render(False).shape == image.shape
    assert c.render(True).shape == (40, 30, 4)


def test_custom_physical_layout_and_copy_count(qtbot, tmp_path):
    dialog = PassportDialog("10x15")
    qtbot.addWidget(dialog)
    dialog.width_mm.setValue(40)
    dialog.height_mm.setValue(50)
    dialog.dpi.setValue(150)
    dialog.copies.setValue(2)
    width, height, dpi, count = dialog.values()
    c = EditorController()
    c._attach(Document.from_image(np.full((80, 60, 4), 100, np.uint8)))
    c.make_custom_sheet(width, height, "10x15", dpi, count)
    assert c.document.dpi == 150
    assert c.document.width == passport.mm_to_px(100, 150)
    assert c.is_dirty
    c.export_pdf(tmp_path / "custom.pdf")
    assert (tmp_path / "custom.pdf").read_bytes().startswith(b"%PDF")
    # Bottom grid row remains white when only the top two tiles are requested.
    assert np.all(c.document.layers[0].pixels[-100:, :, :3] == 255)


def test_invalid_print_layout_is_rejected():
    photo = np.full((40, 30, 4), 120, np.uint8)
    with pytest.raises(ValueError, match="does not fit"):
        passport.build_print_sheet(photo, 200, 300, passport.SHEET_SIZES[0])
    with pytest.raises(ValueError, match="copies"):
        passport.build_print_sheet(photo, 35, 45, passport.SHEET_SIZES[0], copies=1000)
    with pytest.raises(ValueError):
        passport.mm_to_px(-1, 300)


def test_large_processing_rejects_stale_result(qtbot, monkeypatch):
    import photostudio.imaging.beauty as beauty
    started, release = threading.Event(), threading.Event()
    def slow(pixels, amount):
        started.set()
        release.wait(3)
        return np.full_like(pixels, 255)
    monkeypatch.setitem(beauty.BEAUTY_FILTERS, "Portrait Enhance", (slow, {"amount": .5}))
    c = EditorController()
    c.new_document(1000, 1000)
    original = c.document.active_layer.pixels
    c.apply_beauty("Portrait Enhance")
    qtbot.waitUntil(started.is_set)
    c.set_adjustment("brightness", .2)
    release.set()
    qtbot.waitUntil(lambda: c._processing is None)
    assert c.document.active_layer.pixels is original
    c.processing_pool.waitForDone()
