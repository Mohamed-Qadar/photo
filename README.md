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

- Create a new project, open an image (JPG / PNG / WebP / TIFF / BMP), or reopen a `.pstudio` project
- Zoomable / pannable canvas (mouse-wheel zoom, hand-drag pan, fit-to-window)
- Crop (drag on canvas), rotate 90° CW/CCW, flip horizontal/vertical, resize
- Non-destructive brightness & contrast adjustments (stored as layer parameters)
- Full undo / redo, with slider drags coalesced into single steps
- Layer list with show/hide; Properties & Layers side panels
- Save / open native **`.pstudio`** projects (versioned; preserves editable content, never flattens)
- Export to **PNG** and **JPG**, matching the editor preview
- Dark (default) and light themes
- Settings dialog (General + About) and an About window

### Planned (not yet implemented — shown disabled in the app)

- Beauty & portrait studio (skin smoothing, blemish/red-eye, teeth/eye, portrait lighting)
- AI tools (background removal, object removal, subject-aware crop) via local ONNX models
- Social-media design studio (post/story/thumbnail canvases, text, shapes, stickers, templates)
- Advanced typography & graphic-design tools, SVG import/export
- Passport & ID photo studio (country presets, print sheets 10×15 / A4, real DPI, PDF export)
- Full adjustment set (exposure, saturation/vibrance, white balance, curves, sharpen, denoise, …),
  histogram, presets, before/after
- Autosave & crash recovery, batch export

See [ARCHITECTURE.md](ARCHITECTURE.md) §10 for the full phase roadmap.

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

- **1.1.1** — Project identity & Windows distribution setup: app version/attribution, original app
  icon, PyInstaller spec with EXE metadata, Inno Setup installer, GitHub Actions Windows build
  pipeline (tests → build → installer → checksum → artifact, pre-release on tags), full README.
  Core Phase 1 editing (open/crop/rotate/adjust/undo-redo/save/export) implemented and tested.

## License & attribution notes

No third-party branded assets, proprietary UI, or AI models are bundled. Any future on-device model
will be added only after its redistribution license is documented. Inspiration from other tools is
conceptual only; all code and assets here are original.
