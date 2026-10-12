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

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402

from photostudio.ui.main_window import MainWindow  # noqa: E402


def main() -> int:
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

    # Template.
    c.open_template("biz_sale")
    assert c.document is not None and len(c.document.layers) >= 3

    # Home navigation toggles docks.
    win._show_home()
    assert all(not dock.isVisible() for dock in win._docks)

    print("SMOKE OK: window built, design + photo flows ran, export succeeded.")
    app.processEvents()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
