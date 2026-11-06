"""An adapter wraps ONE model family behind a small, tool-friendly API.

To add a model: create adapters/<name>.py with a class called `Adapter`, then add an
entry to models/manifest.json that points at it. Tools never import model libraries
directly; they call ctx.models.get("<model name>") and use the adapter's methods.
"""
from __future__ import annotations

import urllib.request
from pathlib import Path
from typing import Any


def download_file(url: str, dest: Path) -> None:
    """Download `url` to `dest`. The file only appears once it is complete, so a failed
    or blocked download never leaves a broken model file behind."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    try:
        with urllib.request.urlopen(url, timeout=60) as response, open(tmp, "wb") as out:   # noqa: S310
            while chunk := response.read(1 << 20):
                out.write(chunk)
        tmp.replace(dest)
    finally:
        tmp.unlink(missing_ok=True)


class BaseAdapter:
    def __init__(self, name: str, entry: dict[str, Any], device: str, weights_dir: Path):
        self.name = name
        self.entry = entry
        self.device = device
        self.weights_dir = weights_dir

    def load(self) -> None:
        """Load weights / create the underlying model. Raise ModelUnavailable if impossible."""
        raise NotImplementedError

    def unload(self) -> None:
        """Free memory. Optional."""
