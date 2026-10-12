# PhotoStudio — Architecture

> Working name: **PhotoStudio** (temporary). Offline-first Windows 10/11 x64 photo & design studio.
> Stack: Python 3.11+, PySide6 / Qt 6, NumPy, Pillow, OpenCV. Packaged with PyInstaller + Inno Setup.

This document is the source of truth for structure and conventions. It is updated at the end of
every phase alongside the phase report.

## 1. Goals that shape the design

- **Offline-first, no account, no server.** Everything runs locally.
- **Non-destructive editing.** The document keeps editable layers and adjustment parameters;
  export flattens a *copy*, never the document.
- **Undo/redo everywhere.** Every state change is a `Command` pushed onto a per-document `History`.
- **UI thread stays responsive.** Full-resolution pixel work never runs synchronously on the UI
  thread for large images — heavy ops go through the worker layer (`core.jobs`). Phase 1 ships the
  job plumbing; adjustments on the preview use a downscaled proxy.
- **Modular.** `core` (document model, history, IO) and `imaging` (pixel math) have **no Qt/UI
  imports** and are independently testable with pytest. UI depends on them, never the reverse.

## 2. Layered architecture

```
photostudio/
  photostudio/
    app.py            # QApplication bootstrap, launches MainWindow
    core/             # NO Qt imports — pure Python/NumPy, fully unit-tested
      document.py     # Document, Layer, enums (BlendMode, LayerKind)
      commands.py     # Command base + concrete commands (adjust, crop, rotate, flip, resize, layer ops)
      history.py      # History (undo/redo stack, coalescing, change signals via callback)
      pipeline.py     # composite(document) -> RGBA ndarray; applies per-layer adjustments
      project_io.py   # save/load .pstudio (zip: manifest.json + layer PNGs)
      recovery.py     # autosave + crash-recovery scan
      jobs.py         # background job abstraction (QThreadPool-free core interface)
    imaging/          # NO Qt imports — stateless pixel functions on ndarrays
      adjustments.py  # brightness, contrast, (later: exposure, saturation, WB, curves...)
      transforms.py   # crop, rotate90, rotate_arbitrary, flip, resize
      io.py           # load_image / save_image via Pillow (JPG/PNG/WebP/TIFF)
    ui/               # PySide6 — depends on core + imaging
      theme.py        # dark/light QSS + palette tokens
      main_window.py  # menus, docks, toolbar, wiring to a Controller
      controller.py   # bridges UI intents -> Commands on the active Document/History
      home_screen.py  # New / Edit Photo / Passport / ... landing
      canvas.py       # QGraphicsView zoom/pan canvas, renders pipeline output
      panels/         # layers, history, properties/adjustments, color docks
    resources/        # original icons, qss, fonts (no third-party branded assets)
  tests/              # pytest; core + imaging covered without a display
  packaging/          # PyInstaller spec, Inno Setup script (Phase 7)
  run.py              # dev entry point: python run.py
```

## 3. Document model

- **Document**: `width`, `height` (canvas pixels), `dpi`, ordered `layers` (bottom→top), `active_layer_id`.
- **Layer**: `id`, `name`, `kind` (IMAGE | TEXT | SHAPE | ADJUSTMENT — Phase 1 ships IMAGE),
  `pixels` (H×W×4 uint8 RGBA ndarray), `offset` (x,y), `visible`, `opacity` (0..1),
  `blend` (BlendMode), and `adjustments` dict (`{"brightness": 0.0, "contrast": 0.0, ...}`) applied
  **non-destructively** at composite time.
- Rationale: keeping adjustments as parameters (not baked into `pixels`) is what makes editing
  non-destructive and keeps `.pstudio` re-openable with full editability.

## 4. Undo/redo

`Command` has `do()` / `undo()` and a human label. `History` holds two stacks. A command captures the
*inverse state* it needs on construction (e.g. crop stores prior pixels+size). Adjustment slider
drags **coalesce**: consecutive adjustments to the same `(layer, key)` within one interaction merge
into a single undo step. History emits a change callback so the UI refreshes titles/menus.

## 5. Rendering pipeline

`pipeline.composite(document, proxy_scale=1.0)` returns an RGBA ndarray:
1. start with transparent canvas sized to the document,
2. for each visible layer bottom→top: apply its adjustments to a copy, then alpha-blend at `offset`
   using `opacity` and `blend`.
Preview uses a proxy scale for large images; export uses `proxy_scale=1.0`. The canvas converts the
ndarray to `QImage` once per dirty cycle.

## 6. Project format `.pstudio`

A ZIP archive, versioned:
```
manifest.json      # {format_version, app_version, width, height, dpi, layers:[{id,name,kind,offset,
                   #  visible,opacity,blend,adjustments,data:"layers/<id>.png"}], active_layer_id}
layers/<id>.png    # lossless RGBA pixels per layer (editable content preserved; never flattened)
thumbnail.png      # optional preview
```
Loader validates `format_version` and fails loudly on unknown future versions rather than corrupting.

## 7. Export engine

`project_io.export_document(doc, path, fmt, **opts)` composites a flattened copy and writes via
Pillow. Phase 1: PNG (optional transparency) + JPG (quality). Later phases add WebP, PDF, SVG,
DPI-correct print output, and batch export. Export must match the editor preview.

## 8. Concurrency

`core.jobs` defines a `Job` interface; the UI runs jobs on a `QThreadPool` and marshals results back
with Qt signals. Phase 1 keeps slider previews on a downscaled proxy so interaction stays smooth;
the full-res apply runs as a job. This guarantees the UI thread never blocks on large-image math.

## 9. Testing

- `core` and `imaging` are pure and tested headlessly (no `QApplication` needed).
- Coverage targets per the brief: import/export, crop/resize, layer ops, non-destructive edits,
  undo/redo, `.pstudio` round-trip, (later) PDF export, DPI math, crash recovery, installer smoke.
- Qt UI gets lightweight `pytest-qt` smoke tests where a display is available; CI uses a virtual
  display / offscreen Qt platform.

## 10. Phase roadmap (brief §DELIVERY PHASES)

1. **P1 (this delivery):** architecture, shell, home nav, document model, zoomable canvas, open/
   import, crop/rotate, brightness/contrast, undo/redo, save/open `.pstudio`, export PNG/JPG.
2. P2: full core adjustments (exposure, saturation/vibrance, WB, highlights/shadows, curves,
   sharpen/blur/denoise, vignette), histogram, presets, before/after.
3. P3: layers UI depth, shapes, text, social-media canvases, templates.
4. P4: portrait tools + local ONNX models (license-checked).
5. P5: passport/ID studio, print sheets (10×15, A4), real DPI, PDF export.
6. P6: advanced typography/effects, performance, accessibility.
7. P7: QA, PyInstaller + Inno Setup installer, GitHub Actions releases, docs.

## 11. Conventions

- `core`/`imaging` must not `import PySide6`. A test enforces this.
- Pixels are **RGBA uint8**, H×W×4, non-premultiplied, sRGB. Math promotes to float32 then clips.
- No network calls in core paths. No bundled third-party branded assets or models without a
  documented, redistributable license.
