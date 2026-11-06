"""The single entry point used by BOTH the desktop app and the FastAPI backend.

    engine.run("blur", image, {"strength": 12})
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image

from engine.base_tool import ToolContext
from engine.device_manager import DeviceManager
from engine.errors import EngineError
from engine.model_manager import ModelManager
from engine.pipeline import Pipeline
from engine.schemas.responses import ToolInfo
from engine.schemas.validation import validate_params
from engine.tool_registry import ToolRegistry


class Engine:
    def __init__(self, weights_dir: Path | None = None, device: str | None = None):
        self.registry = ToolRegistry()
        self.registry.discover()
        self.devices = DeviceManager(prefer=device)
        self.models = ModelManager(self.devices, weights_dir=weights_dir)

    # ---- discovery -------------------------------------------------------
    def list_tools(self) -> list[str]:
        return self.registry.names()

    def describe_tools(self) -> list[ToolInfo]:
        return self.registry.infos()

    # ---- running ---------------------------------------------------------
    def run(self, tool: str, image: Image.Image, params: dict[str, Any] | None = None) -> Image.Image:
        tool_obj = self.registry.get(tool)
        clean = validate_params(tool_obj.params, params)
        ctx = ToolContext(models=self.models, device=self.devices.device)
        result = tool_obj.run(image, clean, ctx)
        if not isinstance(result, Image.Image):
            raise EngineError(f"Tool '{tool}' did not return an image")
        return result

    def pipeline(self) -> Pipeline:
        return Pipeline(self)


# Module-level shortcut so the backend can write `from engine.engine import run`.
_default: Engine | None = None


def get_engine() -> Engine:
    global _default
    if _default is None:
        _default = Engine()
    return _default


def run(tool: str, image: Image.Image, params: dict[str, Any] | None = None) -> Image.Image:
    return get_engine().run(tool, image, params)
