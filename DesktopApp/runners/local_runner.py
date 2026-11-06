"""Runs tools on this computer by calling the engine directly."""
from __future__ import annotations

from typing import Any

from PIL import Image

from engine.engine import Engine
from engine.errors import EngineError
from engine.schemas.responses import ToolInfo
from runners.base_runner import BaseRunner, RunnerError


class LocalRunner(BaseRunner):
    def __init__(self, engine: Engine):
        self.engine = engine

    def describe_tools(self) -> list[ToolInfo]:
        return self.engine.describe_tools()

    def run(self, tool: str, image: Image.Image, params: dict[str, Any] | None = None) -> Image.Image:
        try:
            return self.engine.run(tool, image, params)
        except EngineError as exc:
            raise RunnerError(str(exc)) from exc

    def close(self) -> None:
        self.engine.models.unload()
