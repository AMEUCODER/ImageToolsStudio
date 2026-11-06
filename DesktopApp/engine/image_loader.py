"""Reading images from disk or bytes into a clean PIL image."""
from __future__ import annotations

import io
from pathlib import Path

from PIL import Image, ImageOps


def _normalize(image: Image.Image) -> Image.Image:
    image = ImageOps.exif_transpose(image)          # respect phone-camera rotation
    if image.mode not in ("RGB", "RGBA"):
        image = image.convert("RGB")
    image.load()                                    # detach from the file handle
    return image


def load_image(path: str | Path) -> Image.Image:
    with Image.open(path) as img:
        return _normalize(img)


def image_from_bytes(data: bytes) -> Image.Image:
    with Image.open(io.BytesIO(data)) as img:
        return _normalize(img)
