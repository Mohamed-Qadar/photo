"""MainWindow — menus, toolbar, docks, canvas/home stack, wiring to controller."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (QDockWidget, QFileDialog, QInputDialog, QMainWindow,
                               QMessageBox, QStackedWidget, QStatusBar, QWidget, QScrollArea, QToolBar, QColorDialog)

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
        from .workers import RenderQueue
        self.render_queue = RenderQueue(self)
        self.render_queue.ready.connect(self._display_render)
        self.render_queue.failed.connect(lambda msg: self.statusBar().showMessage(msg, 8000))
        self._reset_render_view = False

        self._stack = QStackedWidget()
        self.setCentralWidget(self._stack)

        self.home = HomeScreen()
        self.canvas = CanvasView()
        self.canvas.bind_controller(self.controller)
        self._stack.addWidget(self.home)
        self._stack.addWidget(self.canvas)

        self.setStatusBar(QStatusBar())

        self._build_docks()
        self._build_menus()
        self._build_tools()
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
            if widget is self.adjust_panel:
                scroll = QScrollArea()
                scroll.setWidgetResizable(True)
                scroll.setWidget(widget)
                dock.setWidget(scroll)
            else:
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
        m_file.addAction(self._act("Import Image Layer…", self.on_import_image, "Ctrl+Shift+I"))
        m_file.addAction(self._act("Replace Selected Image…", lambda: self.on_import_image(True)))
        m_file.addAction(self._act("Import SVG…", self.on_import_svg))
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
        m_insert.addAction(self._act("Delete Layer", self.controller.delete_selection, "Del"))

        m_arrange = mb.addMenu("&Arrange")
        for label, where in [("Align Left", "left"), ("Align Center", "hcenter"),
                             ("Align Right", "right"), ("Align Top", "top"),
                             ("Align Middle", "vcenter"), ("Align Bottom", "bottom")]:
            m_arrange.addAction(self._act(label, lambda _=False, w=where: self.controller.align_active(w)))
        m_arrange.addSeparator()
        m_arrange.addAction(self._act("Bring Forward", lambda: self.controller.reorder_active(1), "Ctrl+]"))
        m_arrange.addAction(self._act("Send Backward", lambda: self.controller.reorder_active(-1), "Ctrl+["))
        m_arrange.addAction(self._act("Duplicate Layer", self.controller.duplicate_selection, "Ctrl+J"))
        m_arrange.addSeparator()
        m_arrange.addAction(self._act("Group Selected", self.on_group, "Ctrl+G"))
        m_arrange.addAction(self._act("Ungroup", self.controller.ungroup_active, "Ctrl+Shift+G"))

        m_filter = mb.addMenu("&Filter")
        from ..imaging.filters import FILTERS
        for fname in FILTERS:
            m_filter.addAction(self._act(fname, lambda _=False, n=fname: self.controller.apply_filter(n)))

        m_beauty = mb.addMenu("&Beauty")
        from ..imaging.beauty import BEAUTY_FILTERS
        for bname in BEAUTY_FILTERS:
            m_beauty.addAction(self._act(bname, lambda _=False, n=bname: self.controller.apply_beauty(n)))
        m_beauty.addSeparator()
        self.act_heal = QAction("Spot Removal (click skin)", self)
        self.act_heal.setCheckable(True)
        self.act_heal.toggled.connect(self._on_heal_toggled)
        m_beauty.addAction(self.act_heal)

        m_passport = mb.addMenu("&Passport")
        m_passport.addAction(self._act("Replace Background…", self.on_replace_bg))
        m_passport.addAction(self._act("Create 10×15 cm Sheet", lambda: self.on_make_sheet("10x15")))
        m_passport.addAction(self._act("Create A4 Sheet", lambda: self.on_make_sheet("a4")))
        m_passport.addAction(self._act("Export PDF…", self.on_export_pdf))
        self.act_guides = QAction("Show Face Guides", self)
        self.act_guides.setCheckable(True)
        self.act_guides.toggled.connect(self.canvas.set_face_guides)
        m_passport.addAction(self.act_guides)

        m_view = mb.addMenu("&View")
        m_view.addAction(self._act("Zoom In", self.canvas.zoom_in, "Ctrl+="))
        m_view.addAction(self._act("Zoom Out", self.canvas.zoom_out, "Ctrl+-"))
        m_view.addAction(self._act("Fit to Window", self.canvas.fit_to_window, "Ctrl+0"))
        self.act_compare = QAction("Before session", self)
        self.act_compare.setCheckable(True)
        self.act_compare.setShortcut(QKeySequence("\\"))
        self.act_compare.toggled.connect(self._on_compare_toggled)
        m_view.addAction(self.act_compare)
        m_view.addSeparator()
        m_view.addAction(self._act("Dark Theme", lambda: self.apply_theme(dark=True)))
        m_view.addAction(self._act("Light Theme", lambda: self.apply_theme(dark=False)))

        m_help = mb.addMenu("&Help")
        m_help.addAction(self._act("Settings…", self.on_settings))
        m_help.addAction(self._act("About", self.on_about))

    def _build_tools(self):
        self.tools = QToolBar("Tools", self)
        self.tools.setMovable(False)
        self.tools.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, self.tools)
        for title, slot, shortcut in [
            ("Select / Move", self.canvas.cancel_gesture, "V"),
            ("Crop", self.on_begin_crop, "C"),
            ("Text", self.on_add_text, None),
            ("Shape", lambda: self.controller.add_shape(), None),
            ("Image", self.on_import_image, None),
            ("Background", self.on_canvas_background, None),
            ("Templates", self.on_pick_template, None),
            ("Rotate ↻", lambda: self.controller.rotate_90(), None),
            ("Fit canvas", self.canvas.fit_to_window, None)]:
            action = self._act(title, slot, shortcut)
            action.setToolTip(title + (f" ({shortcut})" if shortcut else ""))
            self.tools.addAction(action)
        self.snap_action = QAction("Snapping", self)
        self.snap_action.setCheckable(True)
        self.snap_action.setChecked(True)
        self.snap_action.setToolTip("Snap to canvas and object edges; Space + drag to pan")
        self.snap_action.toggled.connect(lambda value: setattr(self.canvas, "snap_enabled", value))
        self.tools.addAction(self.snap_action)
        self.quick = QToolBar("Project", self)
        self.quick.setMovable(False)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.quick)
        for action in (self.act_save, self.act_export, self.act_undo, self.act_redo, self.act_compare):
            self.quick.addAction(action)
        self.canvas.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.canvas.customContextMenuRequested.connect(self._canvas_menu)

    def _canvas_menu(self, pos):
        from PySide6.QtWidgets import QMenu
        menu = QMenu(self)
        for label, slot in [("Duplicate selected", self.controller.duplicate_selection),
                            ("Delete selected", self.controller.delete_selection),
                            ("Group selected", lambda: self.controller.group_selected(self.controller.selected_ids)),
                            ("Ungroup", self.controller.ungroup_active),
                            ("Add text", self.on_add_text), ("Add shape", lambda: self.controller.add_shape())]:
            menu.addAction(self._act(label, slot))
        menu.exec(self.canvas.mapToGlobal(pos))

    def on_import_image(self, replace=False):
        if self.controller.document is None:
            return
        path, _ = QFileDialog.getOpenFileName(self, "Replace image" if replace else "Import image layer", "", IMAGE_FILTER)
        if path:
            try:
                self.controller.import_image(path, replace=bool(replace))
            except Exception as exc:
                self._error("Could not import image", exc)

    def on_canvas_background(self):
        if self.controller.document is None:
            return
        color = QColorDialog.getColor(parent=self, title="Canvas background")
        if color.isValid():
            self.controller.set_canvas_background([color.red(), color.green(), color.blue(), 255])

    def _wire(self):
        self.home.workspace_selected.connect(self.on_workspace)
        self.controller.processing_error.connect(lambda msg: self.statusBar().showMessage(msg, 8000))

        self.controller.document_changed.connect(self._render)
        self.controller.document_opened.connect(self._on_document_opened)
        self.controller.history_changed.connect(self._update_actions)

        self.canvas.crop_committed.connect(self.controller.crop)
        self.canvas.point_clicked.connect(self._on_canvas_point)
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
        self.tools.hide()
        self.quick.hide()
        self.menuBar().setVisible(True)
        self._update_actions()

    def _show_canvas(self):
        self._stack.setCurrentWidget(self.canvas)
        self._set_docks_visible(True)
        self.tools.show()
        self.quick.show()

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
        elif key == "templates":
            self.on_pick_template()
        elif key == "beauty":
            self.on_open_image()
            if self.controller.document is not None:
                self.statusBar().showMessage(
                    "Beauty Studio: use the Beauty menu (smoothing, enhance, blur, spot removal)", 6000)
        elif key == "passport":
            self.on_open_image()
            if self.controller.document is not None:
                self.statusBar().showMessage(
                    "Passport: Passport menu — replace background, create sheet, export PDF. "
                    "Sizes are examples; verify official requirements.", 8000)

    def on_pick_template(self):
        from .template_picker import TemplatePicker
        picker = TemplatePicker(self)
        if picker.exec() and picker.selected_key() and self._confirm_replace():
            self.controller.open_template(picker.selected_key())

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
        if not self._confirm_replace():
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
        if self._confirm_replace():
            self.controller.new_document(w, h)

    def _on_heal_toggled(self, checked: bool):
        if checked:
            self.canvas.begin_point_tool()
            self.statusBar().showMessage("Click a blemish to remove it (toggle off when done)", 5000)
        else:
            self.canvas.end_point_tool()

    def _on_canvas_point(self, x: int, y: int):
        if getattr(self, "act_heal", None) and self.act_heal.isChecked():
            self.controller.heal_at(x, y, self.adjust_panel.heal_radius.value())
            self.canvas.begin_point_tool()  # stay in heal mode for multiple clicks

    def on_replace_bg(self):
        from PySide6.QtWidgets import QColorDialog
        if self.controller.document is None:
            return
        col = QColorDialog.getColor(parent=self, title="Background colour")
        if col.isValid():
            self.controller.replace_background((col.red(), col.green(), col.blue()))

    def on_make_sheet(self, sheet_key: str):
        from .passport_dialog import PassportDialog
        if self.controller.document is None:
            return
        dialog = PassportDialog(sheet_key, self)
        if not dialog.exec() or not self._confirm_replace():
            return
        width, height, dpi, copies = dialog.values()
        try:
            self.controller.make_custom_sheet(width, height, sheet_key, dpi, copies)
            self.statusBar().showMessage("Preparing print sheet… Export the finished sheet as PDF.", 5000)
        except Exception as exc:
            self._error("Could not create print sheet", exc)

    def on_export_pdf(self):
        if self.controller.document is None:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export PDF", "photo.pdf", "PDF (*.pdf)")
        if path:
            try:
                if not path.lower().endswith(".pdf"):
                    path += ".pdf"
                self.controller.export_pdf(path)
                self.statusBar().showMessage(f"Exported {Path(path).name}", 3000)
            except Exception as exc:  # noqa: BLE001
                self._error("Could not export PDF", exc)

    def on_import_svg(self):
        if self.controller.document is None:
            return
        path, _ = QFileDialog.getOpenFileName(self, "Import SVG", "", "SVG (*.svg)")
        if path:
            try:
                self.controller.import_svg(path)
            except Exception as exc:  # noqa: BLE001
                self._error("Could not import SVG", exc)

    def on_group(self):
        ids = self.layers_panel.selected_layer_ids()
        self.controller.group_selected(ids)

    def on_add_text(self):
        text, ok = QInputDialog.getText(self, "Add Text", "Text:", text="Your text")
        if ok and text:
            self.controller.add_text(text)

    def on_open_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Image", "", IMAGE_FILTER)
        if path and self._confirm_replace():
            try:
                self.controller.open_image(path)
            except Exception as exc:  # noqa: BLE001
                self._error("Could not open image", exc)

    def on_open_project(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Project", "", PROJECT_FILTER)
        if path and self._confirm_replace():
            try:
                self.controller.open_project(path)
            except Exception as exc:  # noqa: BLE001
                self._error("Could not open project", exc)

    def on_save(self):
        if self.controller.project_path is None:
            return self.on_save_as()
        else:
            try:
                self.controller.save_project()
                self.statusBar().showMessage("Project saved", 3000)
                return True
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
                return True
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
        self.act_compare.setChecked(False)
        self.canvas.read_only = False
        self._show_canvas()
        self._render(reset_view=True)
        self._update_title()

    def _on_compare_toggled(self, checked: bool):
        self.canvas.read_only = checked
        self.canvas.cancel_gesture()
        self._render()
        self.statusBar().showMessage("Showing original (before)" if checked
                                     else "Showing edited (after)", 2000)

    def _render(self, reset_view: bool = False):
        use_adj = not (hasattr(self, "act_compare") and self.act_compare.isChecked())
        if self.controller.document is not None:
            self._reset_render_view |= reset_view
            source = self.controller.document if use_adj else self.controller.original_document
            self.render_queue.request(source, True)
        self._update_actions()
        self._update_title()

    def _display_render(self, pixels):
        self.canvas.set_image(pixels, reset_view=self._reset_render_view)
        self._reset_render_view = False

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

    def _confirm_replace(self):
        if not self.controller.is_dirty:
            return True
        answer = QMessageBox.warning(
            self, "Unsaved changes", "Save your changes before continuing?",
            QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard |
            QMessageBox.StandardButton.Cancel, QMessageBox.StandardButton.Save)
        if answer == QMessageBox.StandardButton.Save:
            return bool(self.on_save())
        return answer == QMessageBox.StandardButton.Discard

    def closeEvent(self, event):
        if self._confirm_replace():
            self.render_queue.invalidate()
            self.render_queue.pool.waitForDone()
            self.controller._revision += 1
            self.controller._processing = None
            self.controller.processing_pool.waitForDone()
            self.layers_panel.thumbnails.invalidate()
            self.layers_panel.thumbnails.pool.waitForDone()
            event.accept()
        else:
            event.ignore()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.canvas.cancel_crop()
        super().keyPressEvent(event)
