"""The contract every tool follows. One tool = one folder in engine/tools/."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, ClassVar

from PIL import Image

from engine.model_manager import ModelManager
from engine.schemas.requests import ParamSpec
from engine.schemas.responses import ToolInfo


@dataclass
class ToolContext:
    """Shared services handed to every tool call."""

    models: ModelManager
    device: str


class BaseTool(ABC):
    name: ClassVar[str] = ""          # registry key, also used in /api/tools/<name>
    label: ClassVar[str] = ""         # text shown in the UI
    description: ClassVar[str] = ""
    params: ClassVar[list[ParamSpec]] = []

    @abstractmethod
    def run(self, image: Image.Image, params: dict[str, Any], ctx: ToolContext) -> Image.Image:
        """Return a NEW image. `params` is already validated and has every key filled in."""

    def info(self) -> ToolInfo:
        return ToolInfo(
            name=self.name,
            label=self.label or self.name,
            description=self.description,
            params=list(self.params),
        )
