# PhotoStudio — Architecture (1.2.0)

PhotoStudio is an offline Windows editor using Python 3.11+, PySide6 Essentials,
NumPy, Pillow and OpenCV. No server, account or network is required to edit.

## Structure

- `core/document.py`: document and raster/text/shape layers, DPI and editable specs.
- `core/commands.py`, `history.py`: undoable operations and command coalescing.
- `core/pipeline.py`: full-resolution RGBA compositing with tone adjustments.
- `core/project_io.py`: ZIP projects, editable specs and raster PNGs; PNG/JPG/PDF export.
- `core/templates.py`, `presets.py`: 22 offline templates and social/print canvases.
- `core/arrange.py`, `passport.py`: alignment/snapping and physical print layouts.
- `imaging/`: Qt-free adjustments, filters, portrait processing, rendering and IO.
- `ui/controller.py`: editing intents, locking, history, dirty state and large filter jobs.
- `ui/workers.py`: bounded background render queue and snapshot isolation.
- `ui/canvas.py`: zoom, pan, crop and face guides.
- `ui/main_window.py`: workspace routing, menus, docks, unsaved-change protection.
- `ui/panels/`: layer list, adjustments and text properties.
- `packaging/`, `installer/`, `.github/workflows/`: Windows build and test artifacts.

## Invariants

Core and imaging have no Qt imports. Pixel buffers are H×W×4 uint8 straight RGBA.
Tone adjustments remain parameters; object content remains editable specifications.
Raster filters and transforms replace buffers and preserve undo state. Workers share
immutable pixel references and copy mutable metadata. Widgets and pixmaps are
created only on the UI thread. Preview results carry a revision and stale results
are discarded. Large spatial filters run off the UI thread. Export uses the same
full-resolution pipeline. Lock checks apply to editing intents and grouped moves.

The native `.pstudio` ZIP uses a versioned `manifest.json` and lossless layer PNGs.
Text and shapes store specs, never flattened substitutes. New builds continue to
read older manifests with optional fields omitted.

## Verification and roadmap

Run `python -m pytest` and `python tool/smoke_test.py`. UI tests use Qt offscreen.
The historical first-delivery report is in `docs/PHASE_1_REPORT.md`; ongoing changes
are recorded in `docs/DEVELOPMENT.md`. Interactive object transforms, richer layer
properties, localization, recovery and performance hardening follow the baseline
corrections. Claims about implemented behavior must follow the code and tests.
