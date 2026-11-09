"""The only backend code that touches images and calls engine.run().

Routes stay thin: they pass bytes in and get bytes out. Everything that can go wrong with
an upload (too big, not an image, too many pixels) is turned into a clear HTTP error here.
"""
from __future__ import annotations

import io
import threading
from typing import Any, BinaryIO

from fastapi import HTTPException
from PIL import Image, UnidentifiedImageError

from engine.engine import Engine
from engine.image_exporter import image_to_bytes
from engine.image_loader import image_from_bytes
from settings import Settings

FORMATS = {
    "png": ("PNG", "image/png"),
    "jpeg": ("JPEG", "image/jpeg"),
    "jpg": ("JPEG", "image/jpeg"),
    "webp": ("WEBP", "image/webp"),
}


class ImageService:
    def __init__(self, engine: Engine, settings: Settings):
        self.engine = engine
        self.settings = settings
        self._slots = threading.BoundedSemaphore(settings.max_concurrent)

    # ---- upload -> image ---------------------------------------------------
    def read_upload(self, stream: BinaryIO) -> bytes:
        """Read an upload in chunks so an oversized file is rejected without loading it all."""
        limit = self.settings.max_upload_bytes
        data = bytearray()
        while chunk := stream.read(1 << 20):
            data += chunk
            if len(data) > limit:
                raise HTTPException(413, f"Image is larger than {self.settings.max_upload_mb} MB")
        if not data:
            raise HTTPException(400, "The uploaded file is empty")
        return bytes(data)

    def decode(self, data: bytes) -> Image.Image:
        try:
            with Image.open(io.BytesIO(data)) as probe:             # reads the header only
                width, height = probe.size
            if width * height > self.settings.max_pixels:
                raise HTTPException(
                    413, f"Image is {width}x{height}; the limit is {self.settings.max_pixels // 1_000_000} megapixels"
                )
            return image_from_bytes(data)
        except HTTPException:
            raise
        except (UnidentifiedImageError, Image.DecompressionBombError, OSError, ValueError):
            raise HTTPException(400, "This file is not a readable image (use PNG, JPEG, WebP, BMP or TIFF)") from None

    # ---- run -----------------------------------------------------------------
    def run(self, tool: str, image: Image.Image, params: dict[str, Any]) -> Image.Image:
        if not self._slots.acquire(timeout=self.settings.queue_timeout_s):
            raise HTTPException(503, "The server is busy. Try again in a moment.")
        try:
            return self.engine.run(tool, image, params)
        finally:
            self._slots.release()

    # ---- image -> response ---------------------------------------------------
    @staticmethod
    def encode(image: Image.Image, fmt: str) -> tuple[bytes, str]:
        try:
            pil_format, media_type = FORMATS[fmt.lower()]
        except KeyError:
            raise HTTPException(422, f"Unknown format '{fmt}'. Use png, jpeg or webp.") from None
        return image_to_bytes(image, pil_format), media_type
