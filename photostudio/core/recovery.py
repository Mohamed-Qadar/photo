"""Local recovery projects and preferences; no network or UI dependencies."""
from pathlib import Path
import os


def data_root():
    override = os.environ.get("PHOTOSTUDIO_DATA_DIR")
    root = Path(override) if override else Path(os.environ.get("LOCALAPPDATA", Path.home())) / "PhotoStudio"
    root.mkdir(parents=True, exist_ok=True)
    return root


def recovery_files():
    root = data_root() / "recovery"
    root.mkdir(exist_ok=True)
    return sorted(root.glob("*.pstudio"), key=lambda p: p.stat().st_mtime, reverse=True)
