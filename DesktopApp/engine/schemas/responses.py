"""Data contracts describing what the engine reports back."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from engine.schemas.requests import ParamSpec


@dataclass
class ToolInfo:
    """Public description of a tool. This is what GET /api/tools returns."""

    name: str
    label: str
    description: str = ""
    params: list[ParamSpec] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ToolInfo":
        params = [ParamSpec(**p) for p in data.get("params", [])]
        return cls(
            name=data["name"],
            label=data.get("label", data["name"]),
            description=data.get("description", ""),
            params=params,
        )
