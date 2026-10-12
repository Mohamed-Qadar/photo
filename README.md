# PhotoStudio

**Offline-first photo & design studio for Windows 10/11 (x64).**

> **Version 1.1.1 — in active development (Phase 1 vertical slice).**
> The core photo-editing workflow is implemented and tested; many advanced modules are planned and
> are shown as clearly-disabled tiles in the app until they are built. No fake features.

Built with Python 3.11, PySide6 / Qt 6, NumPy, Pillow and OpenCV.

---

## Overview

PhotoStudio is a desktop application for editing photos and creating designs entirely on your own
computer — no account, no subscription, and no internet connection required. It uses a
non-destructive, layer-based document model so your edits stay re-editable, with full undo/redo and a
native `.pstudio` project format.

## Features

### Implemented (working today)

- **Shared design engine** used by every workspace: raster image layers **plus editable text and
  vector shape objects** (rectangle, rounded, ellipse, triangle, line), each with offset, opacity,
  visibility, locking and blend mode.
- **New Design / Custom Canvas** — blank canvas at any size, add editable text and shapes.
- **Photo Editor** — open an image (JPG / PNG / WebP / TIFF / BMP), zoom/pan, crop (drag), rotate
  90° CW/CCW, flip H/V, resize; non-destructive **exposure, brightness, contrast, saturation,
  temperature, grayscale**; **Gaussian blur & sharpen** filters; **before/after** compare (`\`).
- **Social Media Designer** — real canvas presets (Instagram post/portrait/story, Facebook
  post/cover, YouTube thumbnail, TikTok, WhatsApp Status) using the shared engine.
- **Templates** — 22 original, fully-editable, offline starter designs across Business,
  Education, Restaurant and Events (incl. Somali small-business examples); every element is an
  editable layer; customize and export PNG/JPG.
- **Graphic Design** — preset canvases (A3/A4 poster, flyer, business card, banner, logo) at correct
  DPI, with text and shapes.
- Full **undo / redo** (slider, move and text edits coalesce into single steps).
- Save / open native **`.pstudio`** projects — text & shapes round-trip **editable**, never flattened.
- Export to **PNG** and **JPG**, matching the editor preview.
- Redesigned **home screen** (hero + workspace tiles, no empty panels) and a cleaner editor shell;
  dark (default) and light themes; Settings (General + About) and About window.

### Planned (clearly marked "Soon" in the app — not yet functional)

- **Beauty Studio** — skin smoothing, spot removal, portrait lighting, background blur, before/after.
- **Passport & ID Photo** — face guides, background replacement, 10×15 / A4 print sheets, PDF export.
- **Templates** — 20+ bundled editable starter templates (incl. Somali small-business examples).
- Richer adjustments (saturation, exposure, temperature, sharpen, blur, grayscale, filters),
  on-canvas transform handles & drag, layer thumbnails, masks, SVG import/export, autosave,
  localization (Somali).

See [ARCHITECTURE.md](ARCHITECTURE.md) and the milestone plan for details.

## Screenshots

_Screenshots will be added here once the UI is captured on a release build._

## Download

Pre-built Windows installers are published on the
[**Releases**](https://github.com/Mohamed-Qadar/photo/releases) page when available:

- `PhotoStudio-Setup.exe` — installer (no Python required)
- `PhotoStudio-Setup.exe.sha256` — checksum to verify the download

Verify the download before running:

```powershell
Get-FileHash PhotoStudio-Setup.exe -Algorithm SHA256
```

> Releases during development are published as **pre-releases** and are for testing only.

## Installation (end users)

1. Download `PhotoStudio-Setup.exe` from the Releases page.
2. Run it (a per-user install — no administrator rights needed).
3. Launch PhotoStudio from the Start Menu (or the optional desktop shortcut).

To uninstall, use **Settings → Apps** or the Start Menu uninstaller. Your saved `.pstudio` projects
are **not** deleted on uninstall.

## System requirements

- Windows 10 or 11, 64-bit (x64)
- ~400 MB free disk space for the installed application
- No separate Python installation required for the packaged app

## Run from source (development)

The project runs directly from source — development mode is fully supported.

Easiest: run **`run.bat`**. It checks for Python, creates a virtual environment, installs
dependencies, and launches the app, with clear error messages if anything fails.

Manual equivalent:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe run.py
```

Requires Python 3.11+ on PATH.

## Testing

Run **`test.bat`** (installs `dev-requirements.txt`, then runs pytest with an offscreen Qt platform),
or manually:

```powershell
.\.venv\Scripts\python.exe -m pip install -r dev-requirements.txt
.\.venv\Scripts\python.exe -m pytest
```

The `core` and `imaging` packages are Qt-free and fully unit-tested headlessly; a test enforces that
boundary.

## Building the Windows installer (maintainers)

Handled automatically by GitHub Actions (`.github/workflows/windows-build.yml`) on a Windows runner:
tests → PyInstaller → Inno Setup → SHA-256 → uploaded artifact. Pushing a `v*` tag additionally
publishes a GitHub pre-release. Local build:

```powershell
pip install pyinstaller
pyinstaller packaging\photostudio.spec --noconfirm
iscc installer\photostudio.iss
```

## Developer

**Developed by Eng. Mohamed Ibrahim Abdi — Computer Engineer, specializing in Natural Language
Processing and Computer Vision.**

- Contact: [mohaqadar280@gmail.com](mailto:mohaqadar280@gmail.com)
- GitHub: [https://github.com/Mohamed-Qadar/photo](https://github.com/Mohamed-Qadar/photo)
- Version: 1.1.1

## Version history

- **1.2.0** (in development) — Milestone C: 22 editable offline templates (Business / Education /
  Restaurant / Events, incl. Somali examples), gradient backgrounds, Templates picker. Milestone B:
  extended non-destructive adjustments (exposure,
  saturation, temperature, grayscale) with a Reset, Gaussian blur & sharpen filters, and
  before/after compare. Milestone A: shared design engine with editable **text & shape**
  object layers (render, composite, `.pstudio` persistence, undoable add/move/edit/lock); redesigned
  home screen (hero + tiles, no empty panels / dark rectangles); Social Media & Graphic Design
  workspaces backed by the shared engine with real canvas presets; Insert menu (text/shapes);
  docks hidden on the home screen. 36 automated tests passing.
- **1.1.1** — Project identity & Windows distribution setup: app version/attribution, original app
  icon, PyInstaller spec with EXE metadata, Inno Setup installer, GitHub Actions Windows build
  pipeline (tests → build → installer → checksum → artifact, pre-release on tags), full README.
  Core Phase 1 editing (open/crop/rotate/adjust/undo-redo/save/export) implemented and tested.

## License & attribution notes

No third-party branded assets, proprietary UI, or AI models are bundled. Any future on-device model
will be added only after its redistribution license is documented. Inspiration from other tools is
conceptual only; all code and assets here are original.
