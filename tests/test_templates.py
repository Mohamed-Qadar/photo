"""Milestone C: templates + gradient rendering."""
import numpy as np

from photostudio.core import templates, project_io
from photostudio.core.pipeline import composite
from photostudio.imaging.render import render_gradient


def test_at_least_20_templates():
    assert len(templates.TEMPLATES) >= 20


def test_templates_have_required_categories():
    cats = set(t.category for t in templates.TEMPLATES)
    assert {"Business", "Education", "Restaurant", "Events"}.issubset(cats)


def test_every_template_builds_and_renders():
    for t in templates.TEMPLATES:
        doc = templates.build(t)
        assert doc.width == t.width and doc.height == t.height
        assert len(doc.layers) >= 2          # background + content
        out = composite(doc)
        assert out.shape == (t.height, t.width, 4)
        # Not blank: the rendered design has visible content.
        assert out[..., :3].std() > 1.0


def test_template_elements_are_editable():
    doc = templates.build(templates.get("biz_sale"))
    text_layers = [l for l in doc.layers if l.kind.value == "text"]
    shape_layers = [l for l in doc.layers if l.kind.value == "shape"]
    assert text_layers and shape_layers
    # Text content is editable (spec present, not flattened).
    assert text_layers[0].spec.get("text")
    assert text_layers[0].pixels is None


def test_template_roundtrips_editable(tmp_path):
    doc = templates.build(templates.get("rest_menu"))
    p = tmp_path / "t.pstudio"
    project_io.save_project(doc, p)
    loaded = project_io.load_project(p)
    assert len(loaded.layers) == len(doc.layers)
    tl = [l for l in loaded.layers if l.kind.value == "text"]
    assert tl and tl[0].spec.get("text")


def test_gradient_varies_across_axis():
    g = render_gradient(100, 100, {"angle": 0,
                                   "stops": [[0, [0, 0, 0, 255]], [1, [255, 255, 255, 255]]]})
    assert g.shape == (100, 100, 4)
    assert g[50, 0, 0] < g[50, 99, 0]   # dark -> light left to right


def test_export_template_png(tmp_path):
    doc = templates.build(templates.get("evt_eid"))
    out = tmp_path / "eid.png"
    project_io.export_document(doc, out, fmt="png")
    assert out.exists()
