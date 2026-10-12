"""MainWindow — menus, toolbar, docks, canvas/home stack, wiring to controller."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (QDockWidget, QFileDialog, QInputDialog, QMainWindow,
                               QMessageBox, QStackedWidget, QStatusBar, QWidget)

from .. import (__app_name__, __author__, __author_specialization__,
                __author_title__, __contact_email__, __github_url__, __version__)
from .canvas import CanvasView
from .controller import EditorController
from .home_screen import HomeScreen
from .panels.adjustments_panel import AdjustmentsPanel
from .panels.layers_panel import LayersPanel
from . import theme

IMAGE_FILTER = "Images (*.png *.jpg *.jpeg *.webp *.tif *.tiff *.bmp)"
PROJECT_FILTER = "PhotoStudio Project (*.pstudio)"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(__app_name__)
        self.resize(1280, 820)
        self.controller = EditorController(self)

        self._stack = QStackedWidget()
        self.setCentralWidget(self._stack)

        self.home = HomeScreen()
        self.canvas = CanvasView()
        self._stack.addWidget(self.home)
        self._stack.addWidget(self.canvas)

        self.setStatusBar(QStatusBar())

        self._build_docks()
        self._build_menus()
        self._wire()
        self.apply_theme(dark=True)
        self._show_home()

    # ---- setup --------------------------------------------------------
    def _build_docks(self):
        self.adjust_panel = AdjustmentsPanel(self.controller)
        self.layers_panel = LayersPanel(self.controller)
        self._docks = []
        for widget, title, area in [
            (self.adjust_panel, "Properties", Qt.DockWidgetArea.RightDockWidgetArea),
            (self.layers_panel, "Layers", Qt.DockWidgetArea.RightDockWidgetArea),
        ]:
            dock = QDockWidget(title, self)
            dock.setWidget(widget)
            dock.setObjectName(f"dock_{title.lower()}")
            self.addDockWidget(area, dock)
            self._docks.append(dock)

    def _set_docks_visible(self, visible: bool):
        for dock in self._docks:
            dock.setVisible(visible)

    def _act(self, text, slot, shortcut=None, enabled=True):
        action = QAction(text, self)
        action.triggered.connect(slot)
        if shortcut:
            action.setShortcut(QKeySequence(shortcut))
        action.setEnabled(enabled)
        return action

    def _build_menus(self):
        mb = self.menuBar()

        m_file = mb.addMenu("&File")
        m_file.addAction(self._act("New Project…", self.on_new, "Ctrl+N"))
        m_file.addAction(self._act("Open Image…", self.on_open_image, "Ctrl+O"))
        m_file.addAction(self._act("Open Project…", self.on_open_project, "Ctrl+Shift+O"))
        m_file.addSeparator()
        self.act_save = self._act("Save Project", self.on_save, "Ctrl+S")
        self.act_save_as = self._act("Save Project As…", self.on_save_as, "Ctrl+Shift+S")
        m_file.addAction(self.act_save)
        m_file.addAction(self.act_save_as)
        m_file.addSeparator()
        self.act_export = self._act("Export…", self.on_export, "Ctrl+E")
        m_file.addAction(self.act_export)
        m_file.addSeparator()
        m_file.addAction(self._act("Home", self._show_home))
        m_file.addAction(self._act("Exit", self.close, "Ctrl+Q"))

        m_edit = mb.addMenu("&Edit")
        self.act_undo = self._act("Undo", self.controller.undo, "Ctrl+Z")
        self.act_redo = self._act("Redo", self.controller.redo, "Ctrl+Y")
        m_edit.addAction(self.act_undo)
        m_edit.addAction(self.act_redo)

        m_image = mb.addMenu("&Image")
        self.act_crop = self._act("Crop (drag on canvas)", self.on_begin_crop)
        m_image.addAction(self.act_crop)
        m_image.addAction(self._act("Rotate 90° CW", lambda: self.controller.rotate_90(1)))
        m_image.addAction(self._act("Rotate 90° CCW", lambda: self.controller.rotate_90(-1)))
        m_image.addAction(self._act("Flip Horizontal", lambda: self.controller.flip(True)))
        m_image.addAction(self._act("Flip Vertical", lambda: self.controller.flip(False)))
        m_image.addAction(self._act("Resize…", self.on_resize))

        m_insert = mb.addMenu("&Insert")
        m_insert.addAction(self._act("Text", lambda: self.on_add_text(), "Ctrl+T"))
        m_insert.addSeparator()
        for label, shape in [("Rectangle", "rectangle"), ("Rounded Rectangle", "rounded"),
                             ("Ellipse", "ellipse"), ("Triangle", "triangle"),
                             ("Line", "line")]:
            m_insert.addAction(self._act(label, lambda _=False, s=shape: self.controller.add_shape(s)))
        m_insert.addSeparator()
        m_insert.addAction(self._act("Delete Layer", self.controller.delete_active_layer, "Del"))

        m_view = mb.addMenu("&View")
        m_view.addAction(self._act("Zoom In", self.canvas.zoom_in, "Ctrl+="))
        m_view.addAction(self._act("Zoom Out", self.canvas.zoom_out, "Ctrl+-"))
        m_view.addAction(self._act("Fit to Window", self.canvas.fit_to_window, "Ctrl+0"))
        m_view.addSeparator()
        m_view.addAction(self._act("Dark Theme", lambda: self.apply_theme(dark=True)))
        m_view.addAction(self._act("Light Theme", lambda: self.apply_theme(dark=False)))

        m_help = mb.addMenu("&Help")
        m_help.addAction(self._act("Settings…", self.on_settings))
        m_help.addAction(self._act("About", self.on_about))

    def _wire(self):
        self.home.workspace_selected.connect(self.on_workspace)

        self.controller.document_changed.connect(self._render)
        self.controller.document_opened.connect(self._on_document_opened)
        self.controller.history_changed.connect(self._update_actions)

        self.canvas.crop_committed.connect(self.controller.crop)
        self.canvas.zoom_changed.connect(
            lambda s: self.statusBar().showMessage(f"Zoom {int(s * 100)}%", 2000))

    # ---- theme / nav --------------------------------------------------
    def apply_theme(self, dark: bool):
        self._dark = dark
        tokens = theme.DARK if dark else theme.LIGHT
        self.setStyleSheet(theme.stylesheet(tokens))
        self.canvas.setBackgroundBrush(Qt.GlobalColor.transparent)

    def on_settings(self):
        from .settings_dialog import SettingsDialog
        dlg = SettingsDialog(self, dark=getattr(self, "_dark", True))
        dlg.theme_changed.connect(self.apply_theme)
        dlg.exec()

    def _show_home(self):
        self._stack.setCurrentWidget(self.home)
        self._set_docks_visible(False)          # no empty panels on the home screen
        self.menuBar().setVisible(True)
        self._update_actions()

    def _show_canvas(self):
        self._stack.setCurrentWidget(self.canvas)
        self._set_docks_visible(True)

    # ---- workspace routing -------------------------------------------
    def on_workspace(self, key: str):
        if key in ("new_design", "custom"):
            self.on_new()
        elif key == "photo_editor":
            self.on_open_image()
        elif key == "open_project":
            self.on_open_project()
        elif key in ("social", "graphic"):
            self.on_pick_preset(key)

    def on_pick_preset(self, kind: str):
        from ..core.presets import SOCIAL_PRESETS, GRAPHIC_PRESETS
        presets = SOCIAL_PRESETS if kind == "social" else GRAPHIC_PRESETS
        labels = [p.label for p in presets]
        label, ok = QInputDialog.getItem(
            self, "Choose a canvas",
            "Social media preset:" if kind == "social" else "Graphic design preset:",
            labels, 0, False)
        if not ok:
            return
        preset = presets[labels.index(label)]
        bg = (255, 255, 255, 255)
        self.controller.new_document(preset.width, preset.height, name=preset.label,
                                     background=bg)
        if self.controller.document:
            self.controller.document.dpi = preset.dpi

    # ---- actions ------------------------------------------------------
    def on_new(self):
        w, ok = QInputDialog.getInt(self, "New Design", "Width (px):", 1080, 1, 20000)
        if not ok:
            return
        h, ok = QInputDialog.getInt(self, "New Design", "Height (px):", 1080, 1, 20000)
        if not ok:
            return
        self.controller.new_document(w, h)

    def on_add_text(self):
        text, ok = QInputDialog.getText(self, "Add Text", "Text:", text="Your text")
        if ok and text:
            self.controller.add_text(text)

    def on_open_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Image", "", IMAGE_FILTER)
        if path:
            try:
                self.controller.open_image(path)
            except Exception as exc:  # noqa: BLE001
                self._error("Could not open image", exc)

    def on_open_project(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Project", "", PROJECT_FILTER)
        if path:
            try:
                self.controller.open_project(path)
            except Exception as exc:  # noqa: BLE001
                self._error("Could not open project", exc)

    def on_save(self):
        if self.controller.project_path is None:
            self.on_save_as()
        else:
            try:
                self.controller.save_project()
                self.statusBar().showMessage("Project saved", 3000)
            except Exception as exc:  # noqa: BLE001
                self._error("Could not save", exc)

    def on_save_as(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Project As", "untitled.pstudio",
                                              PROJECT_FILTER)
        if path:
            if not path.endswith(".pstudio"):
                path += ".pstudio"
            try:
                self.controller.save_project(path)
                self.statusBar().showMessage("Project saved", 3000)
                self._update_title()
            except Exception as exc:  # noqa: BLE001
                self._error("Could not save", exc)

    def on_export(self):
        if self.controller.document is None:
            return
        path, selected = QFileDialog.getSaveFileName(
            self, "Export", "export.png",
            "PNG Image (*.png);;JPEG Image (*.jpg)")
        if not path:
            return
        fmt = "jpg" if selected.startswith("JPEG") or path.lower().endswith((".jpg", ".jpeg")) else "png"
        try:
            self.controller.export(path, fmt)
            self.statusBar().showMessage(f"Exported {Path(path).name}", 3000)
        except Exception as exc:  # noqa: BLE001
            self._error("Could not export", exc)

    def on_begin_crop(self):
        self.canvas.begin_crop()
        self.statusBar().showMessage("Crop: drag a rectangle on the canvas (Esc to cancel)", 4000)

    def on_resize(self):
        doc = self.controller.document
        if doc is None:
            return
        w, ok = QInputDialog.getInt(self, "Resize", "Width (px):", doc.width, 1, 20000)
        if not ok:
            return
        h, ok = QInputDialog.getInt(self, "Resize", "Height (px):", doc.height, 1, 20000)
        if not ok:
            return
        self.controller.resize(w, h)

    def on_about(self):
        QMessageBox.about(
            self, "About PhotoStudio",
            f"<h3>{__app_name__}</h3>"
            f"<p>Version {__version__} — offline-first photo &amp; design studio.<br>"
            "Phase 1 vertical slice (in active development).</p>"
            "<hr>"
            f"<p><b>Developed by {__author__}</b><br>"
            f"{__author_title__}, specializing in {__author_specialization__}.</p>"
            f"<p>Contact: <a href='mailto:{__contact_email__}'>{__contact_email__}</a><br>"
            f"GitHub: <a href='{__github_url__}'>{__github_url__}</a></p>")

    # ---- rendering / state -------------------------------------------
    def _on_document_opened(self):
        self._show_canvas()
        self._render(reset_view=True)
        self._update_title()

    def _render(self, reset_view: bool = False):
        pixels = self.controller.render()
        if pixels is not None:
            self.canvas.set_image(pixels, reset_view=reset_view)
        self._update_actions()

    def _update_actions(self):
        has_doc = self.controller.document is not None
        for act in (self.act_save, self.act_save_as, self.act_export, self.act_crop):
            act.setEnabled(has_doc)
        self.act_undo.setEnabled(self.controller.can_undo)
        self.act_redo.setEnabled(self.controller.can_redo)
        if self.controller.history:
            ul = self.controller.history.undo_label()
            rl = self.controller.history.redo_label()
            self.act_undo.setText(f"Undo {ul}".strip())
            self.act_redo.setText(f"Redo {rl}".strip())

    def _update_title(self):
        doc = self.controller.document
        if doc is None:
            self.setWindowTitle(__app_name__)
            return
        name = self.controller.project_path.name if self.controller.project_path else doc.name
        self.setWindowTitle(f"{name} — {__app_name__}")

    def _error(self, message: str, exc: Exception):
        QMessageBox.critical(self, "Error", f"{message}:\n{exc}")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.canvas.cancel_crop()
        super().keyPressEvent(event)
