"""Headless GUI smoke test: construct the real app and exercise key flows.

Runs with the offscreen Qt platform so it needs no display. Verifies that the
MainWindow builds, a design document opens, text + shape objects can be added,
the canvas renders, and an export succeeds — catching UI/engine wiring errors
that unit tests (which don't import Qt) cannot.

Usage:  set QT_QPA_PLATFORM=offscreen & python tool/smoke_test.py
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402

from photostudio.ui.main_window import MainWindow  # noqa: E402


def main() -> int:
    sandbox = tempfile.TemporaryDirectory()
    os.environ["PHOTOSTUDIO_DATA_DIR"] = sandbox.name
    app = QApplication.instance() or QApplication([])
    win = MainWindow()
    win.show()

    c = win.controller
    c.new_document(800, 600, name="Smoke")
    assert c.document is not None and (c.document.width, c.document.height) == (800, 600)

    c.add_text("Hello Somalia")
    c.add_shape("ellipse")
    assert len(c.document.layers) == 3, "expected background + text + shape"

    # Render pipeline (what the canvas shows).
    px = c.render()
    assert px is not None and px.shape == (600, 800, 4)

    # Undo/redo round-trip.
    c.undo(); c.redo()

    # Adjustments + transforms on an image document.
    import numpy as np
    from photostudio.core.document import Document
    c._attach(Document.from_image(np.full((120, 160, 4), 128, np.uint8), name="img"))
    for key in ("exposure", "brightness", "contrast", "saturation", "temperature"):
        c.set_adjustment(key, 0.2)
    c.set_adjustment("grayscale", 0.4)
    c.apply_filter("Gaussian Blur")
    c.apply_filter("Sharpen")
    before = c.render(use_adjustments=False)
    after = c.render(use_adjustments=True)
    assert before is not None and after is not None
    c.crop(10, 10, 100, 80)
    c.rotate_90(1)

    # Export both formats.
    with tempfile.TemporaryDirectory() as d:
        png, jpg = Path(d) / "o.png", Path(d) / "o.jpg"
        c.export(png, "png")
        c.export(jpg, "jpg")
        assert png.exists() and jpg.exists()

    # Graphic-design ops on a design document.
    c.new_document(600, 400, name="Design")
    c.add_shape("rectangle")
    c.align_active("hcenter"); c.align_active("vcenter")
    c.duplicate_active()
    c.set_opacity(0.5)
    c.reorder_active(-1)

    # SVG import (offline, via QtSvg).
    import tempfile as _tf
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64">'
           '<circle cx="32" cy="32" r="28" fill="red"/></svg>')
    with _tf.TemporaryDirectory() as d:
        sp = Path(d) / "x.svg"
        sp.write_text(svg, encoding="utf-8")
        before = len(c.document.layers)
        c.import_svg(sp)
        assert len(c.document.layers) == before + 1, "SVG import should add a layer"

    # Beauty Studio on an image document.
    c._attach(Document.from_image(np.random.randint(60, 200, (120, 120, 4), np.uint8)))
    for bname in ("Skin Smoothing", "Portrait Enhance", "Background Blur"):
        c.apply_beauty(bname)
    c.heal_at(60, 60, 10)
    assert c.render() is not None

    # Passport flow: open image, replace background, make sheet, export PDF.
    c._attach(Document.from_image(np.full((600, 480, 4), 180, np.uint8), name="id"))
    c.replace_background((255, 255, 255))
    c.make_print_sheet("35x45", "10x15", dpi=150)
    assert c.document is not None and c.document.name.startswith("Sheet")
    with tempfile.TemporaryDirectory() as d:
        pdf = Path(d) / "sheet.pdf"
        c.export_pdf(pdf)
        assert pdf.exists()

    # Template.
    c.open_template("biz_sale")
    assert c.document is not None and len(c.document.layers) >= 3

    # Exercise the visible canvas with real Qt mouse events.
    from PySide6.QtCore import QPointF, Qt
    from PySide6.QtTest import QTest
    import time
    def drain():
        deadline = time.monotonic() + 30
        while win.render_queue.running or win.render_queue.pending:
            app.processEvents()
            QTest.qWait(5)
            assert time.monotonic() < deadline, f"preview timed out: running={win.render_queue.running}, pending={win.render_queue.pending is not None}, threads={win.render_queue.pool.activeThreadCount()}"
        app.processEvents()
    c.new_document(600, 400)
    c.document.layers[0].locked = True
    c.add_shape("rectangle")
    shape = c.document.active_layer
    drain()
    win.canvas.set_zoom(1)
    win.canvas.snap_enabled = False
    rect = win.canvas.layer_rect(shape)
    start = win.canvas.mapFromScene(rect.center())
    end = win.canvas.mapFromScene(rect.center() + QPointF(30, 20))
    original = shape.offset
    QTest.mousePress(win.canvas.viewport(), Qt.MouseButton.LeftButton, pos=start)
    QTest.mouseMove(win.canvas.viewport(), end)
    QTest.mouseRelease(win.canvas.viewport(), Qt.MouseButton.LeftButton, pos=end)
    assert shape.offset == (original[0]+30, original[1]+20)
    c.undo()
    assert shape.offset == original
    c.add_text("Dhallinyarada Soomaaliyeed")
    win.adjust_panel.text_input.setText("Soo dhawoow")
    win.adjust_panel.text_input.editingFinished.emit()
    assert c.document.active_layer.spec["text"] == "Soo dhawoow"
    with tempfile.TemporaryDirectory() as d:
        project = Path(d) / "editable.pstudio"
        win._save_project(project)
        win._open_project(project)
        assert c.document.layers[-1].spec["text"] == "Soo dhawoow"
        win._export_file(Path(d)/"design.png", "png")
        win._export_file(Path(d)/"design.jpg", "jpg")
    c.open_template("biz_phone")
    win.change_language("so")
    assert win.menuBar().actions()[0].text() == "&Fayl"
    win.change_language("en")
    assert win.menuBar().actions()[0].text() == "&File"
    # Packaged builds must also load the public key, crypto backend and payment UI.
    from photostudio.ui.license_dialog import LicenseDialog
    from photostudio.core.project_io import export_pixels
    from photostudio.core.licensing import verify_license, LicenseError, encode_part
    from photostudio.core.pipeline import composite
    import numpy as np
    assert not win.license_manager.is_active()
    assert not np.array_equal(export_pixels(c.document, win.license_manager), composite(c.document))
    payment = LicenseDialog(win.license_manager, win)
    payment.show()
    payment.copy_payment.click()
    assert app.clipboard().text() == "0611354800"
    payment.copy_device.click()
    assert app.clipboard().text() == win.license_manager.device_id
    invalid = "PSL1." + encode_part(b"{}") + "." + encode_part(bytes(64))
    payment.key.setPlainText(invalid)
    payment.activate_button.click()
    assert "Invalid license" in payment.message.text()
    try:
        verify_license(invalid, win.license_manager.device_id)
    except LicenseError:
        pass
    else:
        raise AssertionError("Invalid signature accepted")
    app.processEvents()
    # Exercise the actual preview action and close its modal UI automatically.
    from PySide6.QtCore import QTimer
    preview_seen = []
    def close_export_preview():
        modal = app.activeModalWidget()
        if modal and modal.windowTitle() == "Export Preview":
            preview_seen.append(True)
            modal.accept()
        else:
            QTimer.singleShot(10, close_export_preview)
    QTimer.singleShot(10, close_export_preview)
    win.on_export_preview()
    assert preview_seen
    if "--smoke-output" in sys.argv:
        out = Path(sys.argv[sys.argv.index("--smoke-output")+1])
        out.mkdir(parents=True, exist_ok=True)
        payment.grab().save(str(out/"license_dialog_en.png"))
        from PIL import Image
        Image.fromarray(export_pixels(c.document, win.license_manager), "RGBA").save(out/"free_export_preview.png")
        c.open_template("biz_sale")
        c.select([c.document.layers[2].id])
        drain()
        win.canvas.fit_to_window()
        app.processEvents()
        win.grab().save(str(out/"editor_en.png"))
        win._show_home()
        win.change_language("so")
        app.processEvents()
        win.grab().save(str(out/"home_so.png"))
        (out/"smoke_result.txt").write_text("SMOKE OK: photo, design, SVG, portrait, passport, mouse, persistence, exports, localization, watermark, export preview and offline license verification", encoding="utf-8")
    payment.close()
    # Home navigation toggles docks.
    win._show_home()
    assert all(not dock.isVisible() for dock in win._docks)

    c._dirty = False
    win.close()
    app.processEvents()
    print("SMOKE OK: window built, design + photo flows ran, export succeeded.")
    app.processEvents()
    sandbox.cleanup()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
