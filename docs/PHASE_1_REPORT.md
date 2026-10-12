# Phase 1 Report — PhotoStudio

**Scope:** Architecture + a genuinely functional vertical slice, per the brief's EXECUTION RULES
"first working version" list.

## Implemented features

All nine required first-version capabilities:

1. **Create or open a project** — New Project (blank canvas), Open Image, Open Project (`.pstudio`).
2. **Import an image** — JPG/PNG/WebP/TIFF/BMP via Pillow, normalized to RGBA.
3. **Zoomable canvas** — `QGraphicsView` with wheel zoom, pan (hand drag), fit-to-window.
4. **Crop / rotate** — interactive drag-crop on canvas; rotate 90° CW/CCW; flip H/V; resize.
5. **Brightness & contrast** — non-destructive sliders (stored as layer parameters).
6. **Undo / redo** — full command stack; slider drags coalesce into single undo steps.
7. **Save a project** — native versioned `.pstudio` (ZIP of manifest + per-layer PNGs).
8. **Reopen a saved project** — round-trips editable content (layers, adjustments, blend/opacity).
9. **Export as PNG or JPG** — flattened, matching the editor preview.

Plus: dark (default) + light theme, home screen with clearly-disabled future-module tiles,
menu bar (File/Edit/Image/View/Help), layers & properties docks, keyboard shortcuts, status bar.

## Architecture highlights

- Clean split: `core` (model/history/IO) and `imaging` (pixel math) are **Qt-free and unit-tested**;
  `ui` depends on them. A test enforces the no-Qt boundary.
- Non-destructive model: adjustments are layer parameters applied at composite time, never baked in.
- Command pattern + `History` for undo/redo with coalescing.
- Versioned `.pstudio` format that refuses unknown future versions rather than corrupting data.

## Files added

- `ARCHITECTURE.md`, `README.md`, `pyproject.toml`, `requirements.txt`, `.gitignore`, `run.py`
- `photostudio/` — `__init__`, `__main__`, `app.py`
- `photostudio/core/` — `document.py`, `commands.py`, `history.py`, `pipeline.py`, `project_io.py`
- `photostudio/imaging/` — `adjustments.py`, `transforms.py`, `io.py`
- `photostudio/ui/` — `theme.py`, `canvas.py`, `controller.py`, `home_screen.py`, `main_window.py`,
  `qimage_bridge.py`, `panels/adjustments_panel.py`, `panels/layers_panel.py`
- `tests/` — adjustments, transforms, history, project IO, pipeline/model + no-Qt guard
- `packaging/photostudio.spec` (PyInstaller, for Phase 7)

## Tests executed

`python -m pytest` on 2026-10-12 (Python 3.11.9, Windows 11 x64):

```
...........................                                              [100%]
27 passed in 1.13s
```

All 27 tests passed. They run headlessly (no Qt binding required) and cover: brightness/contrast
math + alpha preservation, crop/rotate/flip/resize, undo/redo with slider coalescing, crop-undo
restoring canvas size, `.pstudio` round-trip (single + multi-layer, adjustments preserved), future-
version rejection, PNG/JPG export, non-destructive compositing (stored pixels untouched), hidden-
layer skip, layer-shape validation, and the architecture guard that `core`/`imaging` never import Qt.

## Known limitations

- Adjustments limited to brightness/contrast (Phase 2 adds the full set + histogram/curves).
- Only IMAGE layers exist yet; text/shape/adjustment layers are Phase 3+.
- Crop runs on the active layer and resets canvas to the crop; multi-layer crop is Phase 3.
- Large-image preview proxy and background-job execution are specified (`core.jobs`) but Phase 1
  composites synchronously; this is safe for typical photos and is hardened in Phase 2/6.
- No installer yet (Phase 7); run from source for now.
- Autosave / crash recovery scaffolding is designed in ARCHITECTURE.md but lands in Phase 2.

## Next phase (Phase 2)

Core image editing depth: exposure, saturation/vibrance, white balance, highlights/shadows,
temperature, sharpening, blur, noise reduction, vignette, curves, histogram, presets, before/after
comparison, plus autosave/crash recovery and the background-job proxy pipeline for large images.
