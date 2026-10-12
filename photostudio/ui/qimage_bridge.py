"""Convert between RGBA uint8 ndarrays and QImage/QPixmap."""
from __future__ import annotations

import numpy as np
from PySide6.QtGui import QImage, QPixmap


def ndarray_to_qimage(pixels: np.ndarray) -> QImage:
    """RGBA uint8 H x W x 4 -> QImage (copied so it owns its buffer)."""
    if pixels.ndim != 3 or pixels.shape[2] != 4:
        raise ValueError("expected RGBA H x W x 4")
    arr = np.ascontiguousarray(pixels)
    h, w = arr.shape[:2]
    img = QImage(arr.data, w, h, 4 * w, QImage.Format.Format_RGBA8888)
    return img.copy()


def ndarray_to_qpixmap(pixels: np.ndarray) -> QPixmap:
    return QPixmap.fromImage(ndarray_to_qimage(pixels))


def qimage_to_ndarray(img: QImage) -> np.ndarray:
    """QImage -> RGBA uint8 H x W x 4 (copied)."""
    img = img.convertToFormat(QImage.Format.Format_RGBA8888)
    w, h = img.width(), img.height()
    ptr = img.constBits()
    arr = np.frombuffer(ptr, dtype=np.uint8, count=h * w * 4).reshape(h, w, 4)
    return arr.copy()
