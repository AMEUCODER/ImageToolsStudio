"""Backend settings, read from environment variables.

    IMAGE_STUDIO_TOKEN         if set, every /api/tools request must send "Authorization: Bearer <token>"
    IMAGE_STUDIO_MAX_UPLOAD_MB largest accepted upload (default 25)
    IMAGE_STUDIO_MAX_PIXELS    largest accepted image in pixels, width x height (default 50 million)
    IMAGE_STUDIO_CONCURRENCY   tools that may run at the same time (default 1; models are not always thread-safe)
    IMAGE_STUDIO_QUEUE_TIMEOUT seconds a request waits for a free slot before getting 503 (default 120)
    IMAGE_STUDIO_CORS          comma-separated browser origins allowed to call the API (dev servers by default)
    IMAGE_STUDIO_WEIGHTS_DIR   where downloaded model files are kept (default: inside the engine package)
    IMAGE_STUDIO_DEVICE        force "cpu", "cuda" or "mps" (default: detect)
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _int(name: str, default: int) -> int:
    try:
        return max(1, int(os.environ.get(name, default)))
    except ValueError:
        return default


def _float(name: str, default: float) -> float:
    try:
        return max(0.1, float(os.environ.get(name, default)))
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    token: str = ""
    max_upload_mb: int = 25
    max_pixels: int = 50_000_000
    max_concurrent: int = 1
    queue_timeout_s: float = 120.0
    cors_origins: list[str] = field(default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"])
    weights_dir: Path | None = None
    device: str | None = None

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024


def load_settings() -> Settings:
    origins = os.environ.get("IMAGE_STUDIO_CORS")
    weights = os.environ.get("IMAGE_STUDIO_WEIGHTS_DIR")
    return Settings(
        token=os.environ.get("IMAGE_STUDIO_TOKEN", ""),
        max_upload_mb=_int("IMAGE_STUDIO_MAX_UPLOAD_MB", 25),
        max_pixels=_int("IMAGE_STUDIO_MAX_PIXELS", 50_000_000),
        max_concurrent=_int("IMAGE_STUDIO_CONCURRENCY", 1),
        queue_timeout_s=_float("IMAGE_STUDIO_QUEUE_TIMEOUT", 120.0),
        cors_origins=[o.strip() for o in origins.split(",") if o.strip()] if origins else Settings().cors_origins,
        weights_dir=Path(weights) if weights else None,
        device=os.environ.get("IMAGE_STUDIO_DEVICE") or None,
    )
