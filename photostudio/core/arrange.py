"""Alignment and snapping helpers (pure geometry). No Qt.

Used by the graphic-design workspace to align objects to the canvas and to snap
positions to canvas edges/centre while dragging.
"""
from __future__ import annotations


def align_offset(layer_w: int, layer_h: int, canvas_w: int, canvas_h: int,
                 where: str, current: tuple[int, int]) -> tuple[int, int]:
    """Return a new (x, y) offset aligning a layer to the canvas.

    `where` is one of: left, hcenter, right, top, vcenter, bottom.
    Only the relevant axis changes; the other keeps its current value.
    """
    x, y = current
    if where == "left":
        x = 0
    elif where == "hcenter":
        x = (canvas_w - layer_w) // 2
    elif where == "right":
        x = canvas_w - layer_w
    elif where == "top":
        y = 0
    elif where == "vcenter":
        y = (canvas_h - layer_h) // 2
    elif where == "bottom":
        y = canvas_h - layer_h
    else:
        raise ValueError(f"unknown alignment {where!r}")
    return (x, y)


def snap(value: int, targets: list[int], threshold: int = 12) -> int:
    """Snap `value` to the nearest target within `threshold` pixels."""
    best = value
    best_d = threshold + 1
    for t in targets:
        d = abs(value - t)
        if d <= threshold and d < best_d:
            best, best_d = t, d
    return best


def snap_offset(offset: tuple[int, int], layer_w: int, layer_h: int,
                canvas_w: int, canvas_h: int, threshold: int = 12) -> tuple[int, int]:
    """Snap a layer's top-left offset to canvas edges and centres."""
    x, y = offset
    x_targets = [0, (canvas_w - layer_w) // 2, canvas_w - layer_w]
    y_targets = [0, (canvas_h - layer_h) // 2, canvas_h - layer_h]
    return (snap(x, x_targets, threshold), snap(y, y_targets, threshold))
