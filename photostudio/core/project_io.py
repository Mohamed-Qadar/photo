"""Native .pstudio project format (ZIP) + flattened export. No Qt imports.

.pstudio layout:
    manifest.json      metadata + per-layer params (adjustments, offset, ...)
    layers/<id>.png    lossless RGBA pixels per layer (editable content preserved)
    thumbnail.png      optional small preview

The loader validates FORMAT_VERSION and refuses unknown future versions rather
than silently corrupting a project.
"""
from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image

from .. import __version__
from .document import BlendMode, Document, Layer, LayerKind
from .pipeline import composite
from ..imaging import io as img_io

FORMAT_VERSION = 1
PROJECT_EXTENSION = ".pstudio"


def _pixels_to_png_bytes(pixels: np.ndarray) -> bytes:
    buf = io.BytesIO()
    Image.fromarray(pixels, mode="RGBA").save(buf, format="PNG")
    return buf.getvalue()


def _png_bytes_to_pixels(data: bytes) -> np.ndarray:
    with Image.open(io.BytesIO(data)) as img:
        return np.asarray(img.convert("RGBA"), dtype=np.uint8).copy()


def save_project(document: Document, path: str | Path) -> None:
    path = Path(path)
    manifest = {
        "format_version": FORMAT_VERSION,
        "app_version": __version__,
        "name": document.name,
        "width": document.width,
        "height": document.height,
        "dpi": document.dpi,
        "active_layer_id": document.active_layer_id,
        "layers": [],
    }
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        for layer in document.layers:
            entry = {
                "id": layer.id,
                "name": layer.name,
                "kind": layer.kind.value,
                "offset": list(layer.offset),
                "visible": layer.visible,
                "locked": layer.locked,
                "opacity": layer.opacity,
                "blend": layer.blend.value,
                "adjustments": layer.adjustments,
                "group": layer.group,
            }
            if layer.is_object:
                # Editable object: store its spec, not flattened pixels.
                entry["spec"] = layer.spec
            else:
                data_path = f"layers/{layer.id}.png"
                entry["data"] = data_path
                zf.writestr(data_path, _pixels_to_png_bytes(layer.pixels))
            manifest["layers"].append(entry)
        try:
            thumb = composite(document)
            zf.writestr("thumbnail.png", _pixels_to_png_bytes(_thumb(thumb)))
        except Exception:
            pass  # thumbnail is best-effort, never blocks a save
        zf.writestr("manifest.json", json.dumps(manifest, indent=2))


def _thumb(pixels: np.ndarray, max_side: int = 256) -> np.ndarray:
    img = Image.fromarray(pixels, mode="RGBA")
    img.thumbnail((max_side, max_side))
    return np.asarray(img, dtype=np.uint8).copy()


def load_project(path: str | Path) -> Document:
    path = Path(path)
    with zipfile.ZipFile(path, "r") as zf:
        manifest = json.loads(zf.read("manifest.json"))
        version = manifest.get("format_version")
        if version is None or version > FORMAT_VERSION:
            raise ValueError(
                f"Unsupported .pstudio format_version {version!r} "
                f"(this build supports up to {FORMAT_VERSION})")
        layers: list[Layer] = []
        for entry in manifest["layers"]:
            kind = LayerKind(entry.get("kind", "image"))
            is_object = kind in (LayerKind.TEXT, LayerKind.SHAPE)
            pixels = None if is_object else _png_bytes_to_pixels(zf.read(entry["data"]))
            layers.append(Layer(
                pixels=pixels,
                name=entry.get("name", "Layer"),
                kind=kind,
                id=entry["id"],
                offset=tuple(entry.get("offset", (0, 0))),
                visible=bool(entry.get("visible", True)),
                locked=bool(entry.get("locked", False)),
                opacity=float(entry.get("opacity", 1.0)),
                blend=BlendMode(entry.get("blend", "normal")),
                adjustments=dict(entry.get("adjustments", {})),
                spec=dict(entry.get("spec", {})),
                group=entry.get("group"),
            ))
    return Document(
        width=int(manifest["width"]),
        height=int(manifest["height"]),
        dpi=int(manifest.get("dpi", 72)),
        layers=layers,
        active_layer_id=manifest.get("active_layer_id"),
        name=manifest.get("name", "Untitled"),
    )


def export_document(document: Document, path: str | Path, fmt: str = "png",
                    quality: int = 92, keep_alpha: bool = True) -> None:
    """Flatten a copy and write it. Export matches the editor preview."""
    flat = composite(document)
    fmt = fmt.lower().lstrip(".")
    if fmt in ("png",):
        img_io.save_png(flat, path, keep_alpha=keep_alpha)
    elif fmt in ("jpg", "jpeg"):
        img_io.save_jpg(flat, path, quality=quality)
    else:
        raise ValueError(f"Unsupported export format: {fmt!r}")
