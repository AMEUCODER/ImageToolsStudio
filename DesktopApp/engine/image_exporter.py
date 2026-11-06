"""Writing images to disk or bytes."""
from __future__ import annotations

import io
from pathlib import Path

from PIL import Image

_JPEG_SUFFIXES = {".jpg", ".jpeg"}


def save_image(image: Image.Image, path: str | Path, quality: int = 95) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() in _JPEG_SUFFIXES and image.mode == "RGBA":
        image = image.convert("RGB")               # JPEG has no alpha channel
    image.save(path, quality=quality)
    return path


def image_to_bytes(image: Image.Image, fmt: str = "PNG") -> bytes:
    buffer = io.BytesIO()
    if fmt.upper() in ("JPEG", "JPG") and image.mode == "RGBA":
        image = image.convert("RGB")
    image.save(buffer, format=fmt)
    return buffer.getvalue()
