import numpy as np
from PIL import Image
from photostudio.ui.main_window import MainWindow
from photostudio.ui.template_picker import TemplatePicker
from photostudio.core.pipeline import composite, composite_preview
from photostudio.core import project_io


def test_template_gallery_offline_filter(qtbot):
    picker = TemplatePicker()
    qtbot.addWidget(picker)
    assert picker.list.count() == 62
    picker.category.setCurrentIndex(picker.category.findData("Restaurant"))
    picker._filter("")
    visible = [picker.list.item(i) for i in range(62) if not picker.list.item(i).isHidden()]
    assert len(visible) == 5
    qtbot.waitUntil(lambda: not picker.list.item(0).icon().isNull())
    picker.pool.waitForDone()


def test_design_template_image_replacement_and_export(qtbot, tmp_path):
    win = MainWindow()
    qtbot.addWidget(win)
    c = win.controller
    c.open_template("biz_sale")
    text = next(l for l in c.document.layers if l.kind.value == "text")
    c.select([text.id])
    c.set_text("Dukaanka Cusub")
    c.set_text_property("outline_width", 2)
    c.undo()
    assert "outline_width" not in text.spec
    text.render()
    a, b = tmp_path / "a.png", tmp_path / "b.png"
    Image.new("RGBA", (200, 100), "red").save(a)
    Image.new("RGBA", (100, 200), "blue").save(b)
    c.import_image(a)
    layer = c.document.active_layer
    c.select([layer.id])
    c.import_image(b, replace=True)
    assert layer.display_size == (200, 100)
    assert tuple(layer.pixels[0, 0]) == (0, 0, 255, 255)
    c.undo()
    assert tuple(layer.pixels[0, 0]) == (255, 0, 0, 255)
    c.set_canvas_background([30, 40, 50, 255])
    assert c.document.layers[0].spec["fill"] == [30, 40, 50, 255]
    c.undo()
    # Gradient template keeps an additional editable background when needed.
    assert len(c.document.layers) == 8
    project = tmp_path / "design.pstudio"
    c.save_project(project)
    loaded = project_io.load_project(project)
    assert loaded.layer_by_id(text.id).spec["text"] == "Dukaanka Cusub"
    assert np.array_equal(composite(loaded), composite(c.document))
    preview = composite_preview(c.document, max_side=160)
    assert max(preview.shape[:2]) == 160
    assert c.document.width == 1080 and text.spec["font_size"] == 110
    c._dirty = False
    win.close()
