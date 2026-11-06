"""Chain several tools: output of one step is the input of the next."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from PIL import Image

if TYPE_CHECKING:  # avoid a circular import at runtime
    from engine.engine import Engine


class Pipeline:
    def __init__(self, engine: "Engine"):
        self._engine = engine
        self._steps: list[tuple[str, dict[str, Any]]] = []

    def add(self, tool: str, params: dict[str, Any] | None = None) -> "Pipeline":
        self._steps.append((tool, params or {}))
        return self

    def run(self, image: Image.Image) -> Image.Image:
        for tool, params in self._steps:
            image = self._engine.run(tool, image, params)
        return image
