"""Loads models on first use, keeps them cached, and can unload them."""
from __future__ import annotations

import importlib
import json
import threading
from pathlib import Path
from typing import Any

from engine.device_manager import DeviceManager
from engine.errors import ModelUnavailable

_MODELS_DIR = Path(__file__).resolve().parent / "models"


class ModelManager:
    def __init__(
        self,
        devices: DeviceManager,
        weights_dir: Path | None = None,
        manifest_path: Path | None = None,
    ):
        self.devices = devices
        self.weights_dir = Path(weights_dir) if weights_dir else _MODELS_DIR / "weights"
        manifest_path = Path(manifest_path) if manifest_path else _MODELS_DIR / "manifest.json"
        self._manifest: dict[str, Any] = json.loads(manifest_path.read_text("utf-8"))["models"]
        self._loaded: dict[str, Any] = {}
        self._lock = threading.Lock()

    def available(self) -> list[str]:
        return sorted(self._manifest)

    def get(self, name: str):
        """Return the loaded adapter for `name`, loading it the first time."""
        with self._lock:
            if name in self._loaded:
                return self._loaded[name]
            entry = self._manifest.get(name)
            if entry is None:
                raise ModelUnavailable(f"Model '{name}' is not listed in manifest.json")
            module = importlib.import_module(f"engine.models.adapters.{entry['adapter']}")
            adapter = module.Adapter(name, entry, self.devices.device, self.weights_dir)
            adapter.load()
            self._loaded[name] = adapter
            return adapter

    def unload(self, name: str | None = None) -> None:
        with self._lock:
            names = [name] if name else list(self._loaded)
            for n in names:
                adapter = self._loaded.pop(n, None)
                if adapter is not None:
                    adapter.unload()
