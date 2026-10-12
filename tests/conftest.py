import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import numpy as np
import pytest


@pytest.fixture(autouse=True)
def avoid_modal_teardown(monkeypatch, tmp_path):
    # Tests of prompts override this explicitly. Other tests must never block
    # pytest-qt's window teardown on an interactive save/discard dialog.
    from PySide6.QtWidgets import QMessageBox
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: QMessageBox.StandardButton.Discard)
    monkeypatch.setenv("PHOTOSTUDIO_DATA_DIR", str(tmp_path / "app-data"))


@pytest.fixture
def rgba_gradient():
    """A 64x48 RGBA test image with a horizontal gradient and full alpha."""
    h, w = 48, 64
    img = np.zeros((h, w, 4), dtype=np.uint8)
    ramp = np.linspace(0, 255, w, dtype=np.uint8)
    img[..., 0] = ramp[None, :]
    img[..., 1] = 100
    img[..., 2] = 150
    img[..., 3] = 255
    return img
