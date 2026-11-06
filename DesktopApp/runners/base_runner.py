"""The ONLY thing the desktop UI knows about processing.

A runner answers three questions: what tools exist, what options each has, and
"run this tool on this image". Where the work happens (here or on the server)
is the runner's business.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from PIL import Image

from engine.schemas.responses import ToolInfo


class RunnerError(Exception):
    """Anything that went wrong while running a tool, with a user-readable message."""


class BaseRunner(ABC):
    @abstractmethod
    def describe_tools(self) -> list[ToolInfo]:
        ...

    @abstractmethod
    def run(self, tool: str, image: Image.Image, params: dict[str, Any] | None = None) -> Image.Image:
        ...

    def list_tools(self) -> list[str]:
        return [info.name for info in self.describe_tools()]

    def close(self) -> None:
        """Release resources (connections, models). Optional."""
