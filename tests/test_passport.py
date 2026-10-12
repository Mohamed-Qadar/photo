"""Milestone F: passport/ID — DPI math, background replace, sheets, PDF."""
import numpy as np

from photostudio.core import passport, project_io
from photostudio.core.document import Document


def test_mm_to_px():
    assert passport.mm_to_px(25.4, 300) == 300      # 1 inch
    assert passport.mm_to_px(100, 300) == 1181      # 10 cm @ 300 dpi


def test_sheet_capacity_10x15_fits_multiple():
    sheet = next(s for s in passport.SHEET_SIZES if s.key == "10x15")
    cols, rows = passport.sheet_capacity(35, 45, sheet, dpi=300)
    assert cols >= 2 and rows >= 2        # several 35x45 photos fit on 10x15
    assert cols * rows >= 4


def test_build_print_sheet_dimensions():
    sheet = next(s for s in passport.SHEET_SIZES if s.key == "10x15")
    photo = np.full((400, 300, 4), 120, np.uint8)
    out = passport.build_print_sheet(photo, 35, 45, sheet, dpi=300)
    assert out.shape[0] == passport.mm_to_px(150, 300)
    assert out.shape[1] == passport.mm_to_px(100, 300)
    assert out.shape[2] == 4


def test_replace_background_changes_border():
    # Blue background, red square subject in the center.
    img = np.zeros((60, 60, 4), np.uint8)
    img[..., 2] = 200; img[..., 3] = 255          # blue bg
    img[20:40, 20:40, :3] = [200, 0, 0]           # red subject
    out = passport.replace_background(img, (255, 255, 255), tolerance=50)
    # Corner (background) becomes near-white.
    assert out[0, 0, 0] > 200 and out[0, 0, 1] > 200 and out[0, 0, 2] > 200
    # Subject stays reddish.
    assert out[30, 30, 0] > out[30, 30, 2]


def test_export_pdf(tmp_path):
    img = np.full((100, 80, 4), 200, np.uint8)
    p = tmp_path / "out.pdf"
    passport.export_pdf(img, p, dpi=300)
    assert p.exists() and p.stat().st_size > 0


def test_export_document_pdf(tmp_path):
    doc = Document.from_image(np.full((50, 50, 4), 128, np.uint8), dpi=300)
    p = tmp_path / "doc.pdf"
    project_io.export_document(doc, p, fmt="pdf")
    assert p.exists()
