"""Document and Layer model — the editable, non-destructive project state.

Pure Python + NumPy. No Qt imports (see ARCHITECTURE.md §11).
Pixels are always H x W x 4 uint8 RGBA, non-premultiplied, sRGB.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import numpy as np


class LayerKind(str, Enum):
    IMAGE = "image"
    TEXT = "text"
    SHAPE = "shape"
    ADJUSTMENT = "adjustment"


class BlendMode(str, Enum):
    NORMAL = "normal"
    MULTIPLY = "multiply"
    SCREEN = "screen"


#: Adjustment parameters understood by the pipeline, with their neutral defaults.
#: Keeping these as parameters (not baked into pixels) is what makes editing non-destructive.
ADJUSTMENT_DEFAULTS: dict[str, float] = {
    "brightness": 0.0,   # -1.0 .. 1.0  (additive, scaled)
    "contrast": 0.0,     # -1.0 .. 1.0  (around mid-gray)
    "exposure": 0.0,     # -1.0 .. 1.0  (multiplicative stops)
    "saturation": 0.0,   # -1.0 .. 1.0  (-1 = grayscale, +1 = boosted)
    "temperature": 0.0,  # -1.0 .. 1.0  (- cool/blue, + warm/orange)
    "grayscale": 0.0,    # 0.0 .. 1.0   (mix toward luma)
}


def new_id() -> str:
    return uuid.uuid4().hex[:12]


def blank_pixels(width: int, height: int) -> np.ndarray:
    """Transparent RGBA canvas."""
    return np.zeros((height, width, 4), dtype=np.uint8)


@dataclass
class Layer:
    """A layer in the shared document engine.

    IMAGE layers carry raster ``pixels``. TEXT and SHAPE layers are *editable
    objects*: they carry a ``spec`` dict describing the object and render to
    pixels on demand (see ``render``), so their content stays re-editable and
    round-trips through ``.pstudio`` without being flattened.
    """
    pixels: Optional[np.ndarray] = None     # H x W x 4 uint8 RGBA (IMAGE layers)
    name: str = "Layer"
    kind: LayerKind = LayerKind.IMAGE
    id: str = field(default_factory=new_id)
    offset: tuple[int, int] = (0, 0)        # (x, y) top-left placement on the canvas
    visible: bool = True
    locked: bool = False
    opacity: float = 1.0                    # 0..1
    blend: BlendMode = BlendMode.NORMAL
    adjustments: dict[str, float] = field(default_factory=lambda: dict(ADJUSTMENT_DEFAULTS))
    spec: dict = field(default_factory=dict)  # TEXT/SHAPE object definition
    group: Optional[str] = None               # group id (layers sharing it move together)

    def __post_init__(self) -> None:
        if self.kind == LayerKind.IMAGE:
            self._validate_pixels(self.pixels)
        elif not self.spec:
            raise ValueError(f"{self.kind.value} layer requires a 'spec'")
        merged = dict(ADJUSTMENT_DEFAULTS)
        merged.update(self.adjustments or {})
        self.adjustments = merged
        self.opacity = float(np.clip(self.opacity, 0.0, 1.0))

    @staticmethod
    def _validate_pixels(pixels) -> None:
        if not isinstance(pixels, np.ndarray):
            raise TypeError("Layer.pixels must be a numpy ndarray")
        if pixels.ndim != 3 or pixels.shape[2] != 4:
            raise ValueError("Layer.pixels must be H x W x 4 (RGBA)")
        if pixels.dtype != np.uint8:
            raise ValueError("Layer.pixels must be uint8")

    @property
    def is_object(self) -> bool:
        return self.kind in (LayerKind.TEXT, LayerKind.SHAPE)

    @property
    def width(self) -> int:
        if self.pixels is not None:
            return int(self.pixels.shape[1])
        return int(self.spec.get("width", 0))

    @property
    def height(self) -> int:
        if self.pixels is not None:
            return int(self.pixels.shape[0])
        return int(self.spec.get("height", 0))

    def render(self) -> np.ndarray:
        """Return this layer's RGBA pixels, rendering object layers from spec."""
        if self.kind == LayerKind.IMAGE:
            return self.pixels
        # Imported lazily to keep imaging optional for pure-model use.
        from ..imaging.render import render_object
        return render_object(self.kind, self.spec)

    def has_edits(self) -> bool:
        return any(abs(self.adjustments.get(k, d) - d) > 1e-9
                   for k, d in ADJUSTMENT_DEFAULTS.items())

    def copy(self) -> "Layer":
        return Layer(
            pixels=None if self.pixels is None else self.pixels.copy(),
            name=self.name,
            kind=self.kind,
            id=self.id,
            offset=self.offset,
            visible=self.visible,
            locked=self.locked,
            opacity=self.opacity,
            blend=self.blend,
            adjustments=dict(self.adjustments),
            spec=dict(self.spec),
            group=self.group,
        )


@dataclass
class Document:
    width: int
    height: int
    dpi: int = 72
    layers: list[Layer] = field(default_factory=list)
    active_layer_id: Optional[str] = None
    name: str = "Untitled"

    def __post_init__(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ValueError("Document dimensions must be positive")
        if self.active_layer_id is None and self.layers:
            self.active_layer_id = self.layers[-1].id

    # ---- layer access -------------------------------------------------
    @classmethod
    def from_image(cls, pixels: np.ndarray, name: str = "Untitled", dpi: int = 72) -> "Document":
        """Build a single-layer document from an RGBA image array."""
        Layer._validate_pixels(pixels)
        h, w = pixels.shape[:2]
        layer = Layer(pixels=pixels, name="Background")
        return cls(width=w, height=h, dpi=dpi, layers=[layer],
                   active_layer_id=layer.id, name=name)

    @classmethod
    def blank(cls, width: int, height: int, name: str = "Untitled",
              background: Optional[tuple[int, int, int, int]] = (255, 255, 255, 255),
              dpi: int = 72) -> "Document":
        """A new design document with an optional solid background layer."""
        layers: list[Layer] = []
        if background is not None:
            px = np.zeros((height, width, 4), dtype=np.uint8)
            px[:] = background
            layers.append(Layer(pixels=px, name="Background"))
        return cls(width=width, height=height, dpi=dpi, layers=layers, name=name)

    @staticmethod
    def make_text_layer(text: str, *, width: int, height: int, font_size: int = 48,
                        color=(20, 20, 20, 255), align: str = "center",
                        bold: bool = False, name: Optional[str] = None) -> Layer:
        spec = {"text": text, "width": int(width), "height": int(height),
                "font_size": int(font_size), "color": list(color),
                "align": align, "bold": bool(bold)}
        return Layer(kind=LayerKind.TEXT, spec=spec, name=name or (text[:20] or "Text"))

    @staticmethod
    def make_shape_layer(shape: str, *, width: int, height: int,
                         fill=(91, 140, 255, 255), stroke=None, stroke_width: int = 0,
                         name: Optional[str] = None) -> Layer:
        spec = {"shape": shape, "width": int(width), "height": int(height),
                "fill": list(fill) if fill else None,
                "stroke": list(stroke) if stroke else None,
                "stroke_width": int(stroke_width)}
        return Layer(kind=LayerKind.SHAPE, spec=spec, name=name or shape.capitalize())

    @staticmethod
    def make_gradient_layer(width: int, height: int, stops, angle: float = 90.0,
                            name: str = "Gradient") -> Layer:
        spec = {"shape": "rectangle", "width": int(width), "height": int(height),
                "gradient": {"angle": float(angle), "stops": stops}}
        return Layer(kind=LayerKind.SHAPE, spec=spec, name=name)

    def layer_by_id(self, layer_id: str) -> Optional[Layer]:
        for layer in self.layers:
            if layer.id == layer_id:
                return layer
        return None

    def index_of(self, layer_id: str) -> int:
        for i, layer in enumerate(self.layers):
            if layer.id == layer_id:
                return i
        raise KeyError(layer_id)

    @property
    def active_layer(self) -> Optional[Layer]:
        if self.active_layer_id is None:
            return None
        return self.layer_by_id(self.active_layer_id)

    def add_layer(self, layer: Layer, index: Optional[int] = None) -> None:
        if index is None:
            self.layers.append(layer)
        else:
            self.layers.insert(index, layer)
        self.active_layer_id = layer.id

    def remove_layer(self, layer_id: str) -> Layer:
        idx = self.index_of(layer_id)
        layer = self.layers.pop(idx)
        if self.active_layer_id == layer_id:
            self.active_layer_id = self.layers[-1].id if self.layers else None
        return layer
