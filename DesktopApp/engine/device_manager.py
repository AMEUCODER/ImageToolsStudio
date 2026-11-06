"""Chooses where models run: cuda, mps (Apple) or cpu. Detection is lazy so the
app starts fast even when torch is installed."""
from __future__ import annotations


class DeviceManager:
    def __init__(self, prefer: str | None = None):
        self._device = prefer

    @property
    def device(self) -> str:
        if self._device is None:
            self._device = self._detect()
        return self._device

    @staticmethod
    def _detect() -> str:
        try:
            import torch  # optional dependency
        except Exception:
            return "cpu"
        if torch.cuda.is_available():
            return "cuda"
        mps = getattr(torch.backends, "mps", None)
        if mps is not None and mps.is_available():
            return "mps"
        return "cpu"
