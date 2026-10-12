"""Exact inventory, all forty editable workflows, and visible beginner interactions."""
from collections import Counter
import hashlib
import json
import numpy as np
import pytest
from PIL import Image, ImageDraw
from PySide6.QtCore import Qt, QPointF, QTimer
from PySide6.QtGui import QColor
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QFileDialog, QInputDialog, QMenu, QApplication
from photostudio.core import templates, project_io
from photostudio.core.pipeline import composite_preview
from photostudio.imaging.render import _load_font
from photostudio.ui.controller import EditorController

OLD_KEYS = ('biz_phone','biz_sale','biz_shop_open','biz_service','biz_card','biz_discount_story',
            'edu_school','edu_study_tips','edu_exam','edu_library','rest_menu','rest_special',
            'rest_coffee','rest_delivery','rest_iftar','evt_wedding','evt_conference','evt_sports',
            'evt_charity','evt_eid','evt_youth','evt_announcement')


def test_exactly_forty_added_and_original_twenty_two_unchanged():
    assert len(templates.TEMPLATES) == 62
    assert len(templates.NEW_TEMPLATES) == 40
    assert templates.EXISTING_KEYS == OLD_KEYS
    original = [templates.get(key) for key in OLD_KEYS]
    payload = [(t.key,t.name,t.category,t.width,t.height,t.layers) for t in original]
    assert hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest() == "88264c3d75140b63813d4aa24af8679cdeefe75f3486bdac7e7810e036e0be9d"
    assert len(set(t.key for t in templates.TEMPLATES)) == 62
    assert Counter(t.category for t in templates.NEW_TEMPLATES) == {
        "Football & Sports":6,"Business & Marketing":7,"Ramadan & Islamic Holidays":5,
        "Weddings & Celebrations":5,"Education & Books":5,"Announcements & Civic Information":5,
        "Digital Content":7}


@pytest.mark.parametrize("template",templates.NEW_TEMPLATES,ids=lambda t:t.key)
def test_every_new_template_edit_replace_color_transform_roundtrip_export(qtbot,tmp_path,template):
    c = EditorController()
    c.open_template(template.key)
    doc = c.document
    assert len(doc.layers) >= 6
    text = next(l for l in doc.layers if l.kind.value=="text")
    c.select([text.id])
    original_text = text.spec["text"]
    c.set_text("Dukaanka Magaalada")
    c.undo()
    assert text.spec["text"] == original_text
    c.redo()
    assert text.spec["text"] == "Dukaanka Magaalada"
    photo = next(l for l in doc.layers if l.kind.value=="image" and l.name!="Background")
    c.select([photo.id])
    size,offset,rotation = photo.display_size,photo.offset,photo.rotation
    old_pixels = photo.pixels.copy()
    source = tmp_path/"replacement.png"
    Image.new("RGB",(120,90),"#9c5555").save(source)
    c.import_image(source,replace=True)
    assert photo.display_size == size and photo.offset == offset and photo.rotation == rotation
    assert tuple(photo.pixels[0,0]) == (156,85,85,255)
    c.undo()
    assert np.array_equal(photo.pixels,old_pixels)
    c.redo()
    c.set_canvas_background([245,240,225,255])
    c.set_canvas_gradient([240,230,210,255],[35,65,90,255],45)
    c.undo()
    c.redo()
    assert doc.layers[0].spec["gradient"]["angle"] == 45
    c.select([photo.id])
    from photostudio.core.commands import transform_state
    before = {photo.id:transform_state(photo)}
    after = {photo.id:((offset[0]+10,offset[1]+12),photo.scale_x*.9,photo.scale_y*.9,15)}
    c.transform_selection(before,after)
    assert photo.offset == (offset[0]+10,offset[1]+12) and photo.rotation==15
    c.undo()
    c.redo()
    project = tmp_path/(template.key+".pstudio")
    c.save_project(project)
    loaded = project_io.load_project(project)
    assert loaded.layer_by_id(text.id).spec["text"] == "Dukaanka Magaalada"
    assert loaded.layer_by_id(photo.id).rotation == 15
    assert np.array_equal(composite_preview(loaded,max_side=180),composite_preview(doc,max_side=180))
    index = templates.NEW_TEMPLATES.index(template)
    fmt = ("png","jpg","pdf")[index%3]
    output = tmp_path/(template.key+"."+fmt)
    project_io.export_document(loaded,output,fmt)
    assert output.stat().st_size > 500
    if fmt != "pdf":
        with Image.open(output) as image: assert image.size==(template.width,template.height)
    else:
        assert output.read_bytes().startswith(b"%PDF")


def test_every_new_design_has_fitting_text_original_art_and_distinct_preview():
    hashes = set()
    layouts = set()
    draw = ImageDraw.Draw(Image.new("RGBA",(1,1)))
    for template in templates.NEW_TEMPLATES:
        # Ignore titles, fonts and palettes: forty structural compositions, not retitles.
        layouts.add(json.dumps([(next(k for k in ("bg","gradient","shape","text","art") if k in spec),
                                 spec.get("x"),spec.get("y"),spec.get("w"),spec.get("h")) for spec in template.layers]))
        assert any("art" in spec for spec in template.layers)
        for spec in template.layers:
            if "text" in spec:
                box = draw.multiline_textbbox((0,0),spec["text"],font=_load_font(spec["size"],spec["bold"]))
                assert box[2]-box[0] <= spec["w"],(template.key,spec["text"])
                assert box[3]-box[1] <= spec["h"],(template.key,spec["text"])
                assert 0 <= spec["x"] and spec["x"]+spec["w"] <= template.width
                assert 0 <= spec["y"] and spec["y"]+spec["h"] <= template.height
        preview = composite_preview(templates.build(template),max_side=160)
        assert preview[...,3].min()==255 and preview[...,:3].std()>10
        hashes.add(hashlib.sha256(preview.tobytes()).hexdigest())
    assert len(hashes)==40
    assert len(layouts)==40


def test_visible_template_text_click_photo_background_drag_and_context_menu(qtbot,monkeypatch,tmp_path):
    from photostudio.ui.main_window import MainWindow
    from photostudio.ui.background_dialog import BackgroundDialog
    win = MainWindow()
    qtbot.addWidget(win)
    win.show()
    c = win.controller
    c.open_template("pro_smartphone")
    qtbot.waitUntil(lambda: not win.render_queue.running,timeout=10000)
    win.canvas.fit_to_window()
    win.canvas.snap_enabled=False
    text = next(l for l in c.document.layers if l.kind.value=="text")
    monkeypatch.setattr(QInputDialog,"getMultiLineText",lambda *a:("Dukaanka Cusub",True))
    point = win.canvas.mapFromScene(win.canvas.layer_rect(text).center())
    QTest.mouseDClick(win.canvas.viewport(),Qt.MouseButton.LeftButton,pos=point)
    assert text.spec["text"]=="Dukaanka Cusub"
    photo = next(l for l in c.document.layers if l.name.startswith("Photo ·"))
    image = tmp_path/"phone.png"
    Image.new("RGB",(100,240),"red").save(image)
    monkeypatch.setattr(QFileDialog,"getOpenFileName",lambda *a:(str(image),""))
    point = win.canvas.mapFromScene(win.canvas.layer_rect(photo).center())
    size,offset = photo.display_size,photo.offset
    QTest.mouseClick(win.canvas.viewport(),Qt.MouseButton.LeftButton,pos=point)
    assert tuple(photo.pixels[0,0])==(255,0,0,255) and photo.display_size==size
    c.undo()
    assert tuple(photo.pixels[0,0])!=(255,0,0,255)
    c.select([])
    def choose_background(dialog):
        dialog.mode.setCurrentIndex(1)
        dialog.colors=[QColor("#203040"),QColor("#406050")]
        return 1
    monkeypatch.setattr(BackgroundDialog,"exec",choose_background)
    background_point = win.canvas.mapFromScene(QPointF(1060,1060))
    QTest.mouseClick(win.canvas.viewport(),Qt.MouseButton.LeftButton,pos=background_point)
    assert c.document.layers[0].spec["gradient"]["stops"][0][1]==[32,48,64,255]
    c.select([photo.id])
    start = win.canvas.mapFromScene(win.canvas.layer_rect(photo).center())
    end = win.canvas.mapFromScene(win.canvas.layer_rect(photo).center()+QPointF(30,20))
    QTest.mousePress(win.canvas.viewport(),Qt.MouseButton.LeftButton,pos=start)
    QTest.mouseMove(win.canvas.viewport(),end)
    QTest.mouseRelease(win.canvas.viewport(),Qt.MouseButton.LeftButton,pos=end)
    assert abs(photo.offset[0]-offset[0]-30)<=2
    menus=[]
    def inspect_menu():
        menu = QApplication.activePopupWidget()
        assert isinstance(menu,QMenu)
        menus.append([action.text() for action in menu.actions()])
        menu.close()
    QTimer.singleShot(0,inspect_menu)
    win._canvas_menu(win.canvas.mapFromScene(win.canvas.layer_rect(photo).center()))
    assert {"Edit","Replace Image…","Duplicate selected","Delete selected","Bring Forward","Send Backward","Lock"}.issubset(set(menus[0]))
    c.set_locked(photo.id,True)
    QTimer.singleShot(0,inspect_menu)
    win._canvas_menu(win.canvas.mapFromScene(win.canvas.layer_rect(photo).center()))
    assert "Unlock" in menus[-1]
    c._dirty=False
    win.close()


def test_browser_category_search_preview_and_use_template(qtbot):
    from photostudio.ui.template_picker import TemplatePicker
    picker = TemplatePicker()
    qtbot.addWidget(picker)
    picker.show()
    picker.category.setCurrentIndex(picker.category.findData("Football & Sports"))
    visible = [item for item in picker.items.values() if not item.isHidden()]
    assert len(visible)==6 and picker.use_button.isEnabled()
    picker.search.setText("Lineup")
    assert picker.selected_key()=="pro_starting_lineup"
    qtbot.waitUntil(lambda:not picker.items["pro_starting_lineup"].icon().isNull(),timeout=15000)
    assert picker.preview.pixmap() and not picker.preview.pixmap().isNull()
    picker.search.setText("no such design")
    assert picker.selected_key() is None and not picker.use_button.isEnabled()
    picker.search.setText("Match Results")
    assert picker.selected_key()=="pro_match_results"
    picker.use_button.click()
    assert picker.result()==1
