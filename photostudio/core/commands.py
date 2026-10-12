"""Undoable commands. Each captures the inverse state it needs. No Qt imports."""
from __future__ import annotations

from typing import Optional

import numpy as np

from .document import Document, Layer
from ..imaging import transforms


class Command:
    """Base class. Subclasses implement do()/undo() and set a label."""
    label: str = "Edit"

    def do(self) -> None:  # pragma: no cover - abstract
        raise NotImplementedError

    def undo(self) -> None:  # pragma: no cover - abstract
        raise NotImplementedError

    def merge_with(self, other: "Command") -> bool:
        """Return True if `other` was folded into this command (coalescing)."""
        return False


class AdjustmentCommand(Command):
    """Set one adjustment parameter on a layer; coalesces repeated drags."""

    def __init__(self, layer: Layer, key: str, new_value: float):
        self.layer = layer
        self.key = key
        self.old_value = float(layer.adjustments.get(key, 0.0))
        self.new_value = float(new_value)
        self.label = f"Adjust {key}"

    def do(self) -> None:
        self.layer.adjustments[self.key] = self.new_value

    def undo(self) -> None:
        self.layer.adjustments[self.key] = self.old_value

    def merge_with(self, other: "Command") -> bool:
        if (isinstance(other, AdjustmentCommand)
                and other.layer is self.layer and other.key == self.key):
            # Keep original old_value, adopt the latest new_value.
            self.new_value = other.new_value
            self.layer.adjustments[self.key] = self.new_value
            return True
        return False


class _PixelSwapCommand(Command):
    """Base for ops that replace a layer's pixels (and possibly document size)."""

    def __init__(self, document: Document, layer: Layer, new_pixels: np.ndarray,
                 resize_canvas: bool, label: str):
        self.document = document
        self.layer = layer
        self.old_pixels = layer.pixels
        self.new_pixels = new_pixels
        self.resize_canvas = resize_canvas
        self.old_size = (document.width, document.height)
        self.new_size = (new_pixels.shape[1], new_pixels.shape[0])
        self.old_offset = layer.offset
        self.label = label

    def do(self) -> None:
        self.layer.pixels = self.new_pixels
        if self.resize_canvas:
            self.document.width, self.document.height = self.new_size
            self.layer.offset = (0, 0)

    def undo(self) -> None:
        self.layer.pixels = self.old_pixels
        if self.resize_canvas:
            self.document.width, self.document.height = self.old_size
            self.layer.offset = self.old_offset


class CropCommand(_PixelSwapCommand):
    def __init__(self, document: Document, layer: Layer, x: int, y: int, w: int, h: int):
        cropped = transforms.crop(layer.pixels, x, y, w, h)
        super().__init__(document, layer, cropped, resize_canvas=True, label="Crop")


class Rotate90Command(_PixelSwapCommand):
    def __init__(self, document: Document, layer: Layer, turns: int = 1):
        rotated = transforms.rotate_90(layer.pixels, turns)
        super().__init__(document, layer, rotated, resize_canvas=True,
                         label="Rotate 90°")


class FlipCommand(_PixelSwapCommand):
    def __init__(self, document: Document, layer: Layer, horizontal: bool):
        flipped = (transforms.flip_horizontal(layer.pixels) if horizontal
                   else transforms.flip_vertical(layer.pixels))
        super().__init__(document, layer, flipped, resize_canvas=False,
                         label="Flip Horizontal" if horizontal else "Flip Vertical")


class ResizeCommand(_PixelSwapCommand):
    def __init__(self, document: Document, layer: Layer, width: int, height: int):
        resized = transforms.resize(layer.pixels, width, height)
        super().__init__(document, layer, resized, resize_canvas=True, label="Resize")


class SetLayerVisibilityCommand(Command):
    def __init__(self, layer: Layer, visible: bool):
        self.layer = layer
        self.old = layer.visible
        self.new = visible
        self.label = "Show Layer" if visible else "Hide Layer"

    def do(self) -> None:
        self.layer.visible = self.new

    def undo(self) -> None:
        self.layer.visible = self.old
