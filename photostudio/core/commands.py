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


class CompositeCommand(Command):
    """One undo step for a multi-object action; gesture boundaries do not merge."""
    def __init__(self, commands, label="Edit Selection"):
        self.commands, self.label = list(commands), label

    def do(self):
        for command in self.commands:
            command.do()

    def undo(self):
        for command in reversed(self.commands):
            command.undo()


def transform_state(layer):
    return (layer.offset, layer.scale_x, layer.scale_y, layer.rotation)


def set_transform(layer, state):
    layer.offset, layer.scale_x, layer.scale_y, layer.rotation = state


class TransformSelectionCommand(Command):
    def __init__(self, layers, before, after, label="Transform Selection"):
        self.layers, self.before, self.after, self.label = layers, before, after, label

    def do(self):
        for layer in self.layers:
            set_transform(layer, self.after[layer.id])

    def undo(self):
        for layer in self.layers:
            set_transform(layer, self.before[layer.id])


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


class AddLayerCommand(Command):
    def __init__(self, document: Document, layer: Layer, index=None):
        self.document = document
        self.layer = layer
        self.index = index
        self.prev_active = document.active_layer_id
        self.label = f"Add {layer.kind.value.capitalize()}"

    def do(self) -> None:
        self.document.add_layer(self.layer, self.index)

    def undo(self) -> None:
        self.document.remove_layer(self.layer.id)
        self.document.active_layer_id = self.prev_active


class RemoveLayerCommand(Command):
    def __init__(self, document: Document, layer: Layer):
        self.document = document
        self.layer = layer
        self.index = document.index_of(layer.id)
        self.prev_active = document.active_layer_id
        self.label = "Delete Layer"

    def do(self) -> None:
        self.document.remove_layer(self.layer.id)

    def undo(self) -> None:
        self.document.add_layer(self.layer, self.index)
        self.document.active_layer_id = self.prev_active


class MoveLayerCommand(Command):
    """Move a layer by (dx, dy); coalesces during a drag."""

    def __init__(self, layer: Layer, new_offset: tuple[int, int]):
        self.layer = layer
        self.old_offset = layer.offset
        self.new_offset = new_offset
        self.label = "Move Layer"

    def do(self) -> None:
        self.layer.offset = self.new_offset

    def undo(self) -> None:
        self.layer.offset = self.old_offset

    def merge_with(self, other: "Command") -> bool:
        if isinstance(other, MoveLayerCommand) and other.layer is self.layer:
            self.new_offset = other.new_offset
            self.layer.offset = self.new_offset
            return True
        return False


class ReorderLayerCommand(Command):
    """Move a layer up/down in z-order (delta +1 = up/toward top)."""

    def __init__(self, document: Document, layer: Layer, delta: int):
        self.document = document
        self.layer = layer
        self.old_index = document.index_of(layer.id)
        self.new_index = max(0, min(len(document.layers) - 1, self.old_index + delta))
        self.label = "Raise Layer" if delta > 0 else "Lower Layer"

    def _move(self, src: int, dst: int):
        layer = self.document.layers.pop(src)
        self.document.layers.insert(dst, layer)

    def do(self) -> None:
        self._move(self.old_index, self.new_index)

    def undo(self) -> None:
        self._move(self.new_index, self.old_index)


class DuplicateLayerCommand(Command):
    def __init__(self, document: Document, layer: Layer):
        self.document = document
        self.source = layer
        self.copy = layer.copy()
        from .document import new_id
        self.copy.id = new_id()
        self.copy.name = f"{layer.name} copy"
        ox, oy = layer.offset
        self.copy.offset = (ox + 16, oy + 16)
        self.label = "Duplicate Layer"

    def do(self) -> None:
        idx = self.document.index_of(self.source.id) + 1
        self.document.add_layer(self.copy, idx)

    def undo(self) -> None:
        self.document.remove_layer(self.copy.id)


class SetOpacityCommand(Command):
    def __init__(self, layer: Layer, opacity: float):
        self.layer = layer
        self.old = layer.opacity
        self.new = max(0.0, min(1.0, float(opacity)))
        self.label = "Set Opacity"

    def do(self) -> None:
        self.layer.opacity = self.new

    def undo(self) -> None:
        self.layer.opacity = self.old

    def merge_with(self, other: "Command") -> bool:
        if isinstance(other, SetOpacityCommand) and other.layer is self.layer:
            self.new = other.new
            self.layer.opacity = self.new
            return True
        return False


class GroupCommand(Command):
    """Assign a shared group id to several layers (or clear it to ungroup)."""

    def __init__(self, layers: list[Layer], group_id):
        self.layers = layers
        self.old = {l.id: l.group for l in layers}
        self.group_id = group_id
        self.label = "Group" if group_id else "Ungroup"

    def do(self) -> None:
        for l in self.layers:
            l.group = self.group_id

    def undo(self) -> None:
        for l in self.layers:
            l.group = self.old[l.id]


class AlignCommand(Command):
    """Align a layer to the canvas on one axis."""

    def __init__(self, document: Document, layer: Layer, where: str):
        from .arrange import align_offset
        self.layer = layer
        self.old_offset = layer.offset
        self.new_offset = align_offset(layer.width, layer.height,
                                       document.width, document.height,
                                       where, layer.offset)
        self.label = f"Align {where}"

    def do(self) -> None:
        self.layer.offset = self.new_offset

    def undo(self) -> None:
        self.layer.offset = self.old_offset


class SetTextPropertyCommand(Command):
    """Edit a text layer's typography (font_size/color/align/bold)."""

    def __init__(self, layer: Layer, key: str, value):
        self.layer = layer
        self.key = key
        self.old = layer.spec.get(key)
        self.new = value
        self.label = f"Text {key}"

    def do(self) -> None:
        self.layer.spec[self.key] = self.new

    def undo(self) -> None:
        self.layer.spec[self.key] = self.old


class MoveGroupCommand(Command):
    """Move all layers sharing a group by the same (dx, dy)."""

    def __init__(self, layers: list[Layer], dx: int, dy: int):
        self.layers = layers
        self.dx, self.dy = int(dx), int(dy)
        self.label = "Move Group"

    def do(self) -> None:
        for l in self.layers:
            l.offset = (l.offset[0] + self.dx, l.offset[1] + self.dy)

    def undo(self) -> None:
        for l in self.layers:
            l.offset = (l.offset[0] - self.dx, l.offset[1] - self.dy)


class SetLayerLockCommand(Command):
    def __init__(self, layer: Layer, locked: bool):
        self.layer = layer
        self.old = layer.locked
        self.new = locked
        self.label = "Lock Layer" if locked else "Unlock Layer"

    def do(self) -> None:
        self.layer.locked = self.new

    def undo(self) -> None:
        self.layer.locked = self.old


class SetTextCommand(Command):
    """Edit a text layer's string (coalesces while typing)."""

    def __init__(self, layer: Layer, new_text: str):
        self.layer = layer
        self.old = layer.spec.get("text", "")
        self.new = new_text
        self.label = "Edit Text"

    def do(self) -> None:
        self.layer.spec["text"] = self.new

    def undo(self) -> None:
        self.layer.spec["text"] = self.old

    def merge_with(self, other: "Command") -> bool:
        if isinstance(other, SetTextCommand) and other.layer is self.layer:
            self.new = other.new
            self.layer.spec["text"] = self.new
            return True
        return False


class FilterCommand(_PixelSwapCommand):
    """Apply a spatial filter function to a raster layer's pixels (undoable)."""

    def __init__(self, document: Document, layer: Layer, func, label: str, **kwargs):
        if layer.pixels is None:
            raise ValueError("Filters apply to raster layers only")
        result = func(layer.pixels, **kwargs)
        super().__init__(document, layer, result, resize_canvas=False, label=label)


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
