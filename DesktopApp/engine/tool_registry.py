"""Finds every tool in engine/tools/ automatically.

Adding a tool = adding a folder with a tool.py that defines a BaseTool subclass.
A tool that fails to import is skipped and reported in `registry.failed`, so one
broken tool never stops the app from starting.
"""
from __future__ import annotations

import importlib
import importlib.util
import pkgutil

import engine.tools as tools_package
from engine.base_tool import BaseTool
from engine.errors import ToolNotFound
from engine.schemas.responses import ToolInfo


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, BaseTool] = {}
        self.failed: dict[str, str] = {}

    def register(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool

    def discover(self) -> None:
        for module_info in pkgutil.iter_modules(tools_package.__path__):
            if not module_info.ispkg:
                continue
            module_name = f"{tools_package.__name__}.{module_info.name}.tool"
            if importlib.util.find_spec(module_name) is None:
                continue                      # folder exists but has no tool.py yet
            try:
                module = importlib.import_module(module_name)
            except Exception as exc:          # noqa: BLE001 - report, don't crash
                self.failed[module_info.name] = repr(exc)
                continue
            for obj in vars(module).values():
                if (
                    isinstance(obj, type)
                    and issubclass(obj, BaseTool)
                    and obj is not BaseTool
                    and obj.__module__ == module.__name__
                    and obj.name
                ):
                    self.register(obj())

    def get(self, name: str) -> BaseTool:
        try:
            return self._tools[name]
        except KeyError:
            raise ToolNotFound(f"Unknown tool '{name}'. Available: {self.names()}") from None

    def names(self) -> list[str]:
        return sorted(self._tools)

    def infos(self) -> list[ToolInfo]:
        return [self._tools[n].info() for n in self.names()]
