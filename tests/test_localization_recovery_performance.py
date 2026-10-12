import threading
import json
import zipfile
import numpy as np
import pytest
from PySide6.QtCore import QThread, Qt, QPointF
from PySide6.QtWidgets import QLabel, QMessageBox, QInputDialog
from photostudio.ui.main_window import MainWindow
from photostudio.ui import i18n
from photostudio.core import project_io
from photostudio.core.document import Document
from photostudio.core.pipeline import composite_preview
from photostudio.core.recovery import recovery_files, data_root


def test_live_somali_language_keeps_document_and_history(qtbot):
    win = MainWindow()
    qtbot.addWidget(win)
    c = win.controller
    c.new_document(300, 200)
    c.add_text("Dhallinyarada Soomaaliyeed")
    doc, history = c.document, c.history
    win.change_language("so")
    assert win.menuBar().actions()[0].text() == "&Fayl"
    assert win.adjust_panel.bold.text() == "Far culus"
    assert win.adjust_panel.text_align.currentText() == "bartamaha"
    assert i18n.tr("Save your changes before continuing?").startswith("Ma kaydinaysaa")
    assert c.document is doc and c.history is history
    assert c.document.active_layer.spec["text"] == "Dhallinyarada Soomaaliyeed"
    win.adjust_panel.text_align.setCurrentText("bidix")
    assert c.document.active_layer.spec["align"] == "left"
    win.change_language("en")
    assert win.menuBar().actions()[0].text() == "&File"
    assert win.adjust_panel.bold.text() == "Bold"
    c._dirty = False
    win.close()


def test_autosave_reopens_editable_document_and_normal_close_cleans(qtbot):
    win = MainWindow()
    qtbot.addWidget(win)
    win.controller.open_template("biz_phone")
    text = next(l for l in win.controller.document.layers if l.kind.value == "text")
    win.controller.select([text.id])
    win.controller.set_text("Dukaanka Telefoonnada Cusub")
    win.autosave.write()
    qtbot.waitUntil(lambda: win.autosave.path.exists() and not win.autosave.running)
    loaded = project_io.load_project(win.autosave.path)
    assert loaded.layer_by_id(text.id).spec["text"] == "Dukaanka Telefoonnada Cusub"
    assert win.controller.is_dirty  # autosave is recovery, not an explicit user save
    path = win.autosave.path
    win.controller._dirty = False
    win.close()
    assert not path.exists()


def test_recovery_prompt_loads_unsaved_project(qtbot, monkeypatch):
    root = data_root() / "recovery"
    root.mkdir()
    path = root / "interrupted.pstudio"
    doc = Document.blank(100, 80)
    doc.add_layer(Document.make_text_layer("Soo dhawoow", width=100, height=30))
    project_io.save_project(doc, path)
    win = MainWindow()
    qtbot.addWidget(win)
    monkeypatch.setattr(QInputDialog, "getItem", lambda *args: (path.name, True))
    win._offer_recovery()
    assert win.controller.document.layers[-1].spec["text"] == "Soo dhawoow"
    assert win.controller.project_path is None and win.controller.is_dirty
    assert path.exists()
    win.controller._dirty = False
    win.close()
    assert not path.exists()


def test_atomic_failure_keeps_existing_project(tmp_path, monkeypatch):
    path = tmp_path / "saved.pstudio"
    doc = Document.blank(20, 20)
    project_io.save_project(doc, path)
    original = path.read_bytes()
    def fail(doc, temp):
        from pathlib import Path
        Path(temp).write_bytes(b"partial")
        raise OSError("Disk full")
    monkeypatch.setattr(project_io, "_write_project", fail)
    with pytest.raises(OSError):
        project_io.save_project(doc, path)
    assert path.read_bytes() == original
    assert list(tmp_path.iterdir()) == [path]


def test_large_preview_coordinates_and_worker_file_io(qtbot, tmp_path):
    win = MainWindow()
    qtbot.addWidget(win)
    c = win.controller
    c.new_document(3200, 2400)
    source = c.document.layers[0].pixels
    preview = composite_preview(c.document, max_side=800)
    assert preview.shape == (600, 800, 4)
    assert c.document.layers[0].pixels is source
    win.canvas.set_image(preview, document_size=(3200, 2400))
    assert win.canvas._pixmap_item.sceneBoundingRect().width() == 3200
    ui_thread = QThread.currentThread()
    worker_thread = win.file_jobs.run(lambda: QThread.currentThread(), "Saving…")
    assert worker_thread != ui_thread
    project = tmp_path / "saved.pstudio"
    win._save_project(project)
    assert not c.is_dirty and project.exists()
    assert str(project.resolve()) in win.settings.value("recent", [], type=list)
    win.close()


def test_old_manifest_and_version_consistency(tmp_path):
    from pathlib import Path
    import tomllib
    from photostudio import __version__
    root = Path(__file__).resolve().parents[1]
    assert tomllib.loads((root / "pyproject.toml").read_text())['project']['version'] == __version__ == "1.2.0"
    path = tmp_path / "old.pstudio"
    project_io.save_project(Document.blank(20, 10), path)
    with zipfile.ZipFile(path) as archive:
        files = {name: archive.read(name) for name in archive.namelist()}
    manifest = json.loads(files['manifest.json'])
    for layer in manifest['layers']:
        for field in ('scale_x', 'scale_y', 'rotation', 'locked', 'group'):
            layer.pop(field, None)
    files['manifest.json'] = json.dumps(manifest).encode()
    with zipfile.ZipFile(path, "w") as archive:
        for name, data in files.items(): archive.writestr(name, data)
    loaded = project_io.load_project(path)
    assert loaded.layers[0].scale_x == 1 and loaded.layers[0].rotation == 0


def test_oversized_canvas_rejected_before_allocation():
    with pytest.raises(ValueError, match="40 megapixels"):
        Document.blank(20000, 20000)
