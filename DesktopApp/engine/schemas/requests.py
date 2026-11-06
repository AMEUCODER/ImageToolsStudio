"""Data contracts describing what a tool accepts. Shared by the UI and the API."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ParamSpec:
    """One option of a tool. The desktop UI and the PWA both build controls from this.

    kind:
      "slider"  float between min and max (optional step)
      "int"     integer between min and max
      "choice"  one of `choices`
      "bool"    on/off switch
      "text"    short text (max = max length, default 200)
      "color"   hex color such as "#ff8800"
    """

    name: str
    label: str
    kind: str
    default: Any
    min: float | None = None
    max: float | None = None
    step: float | None = None
    choices: list[str] = field(default_factory=list)
    help: str = ""


@dataclass
class RunRequest:
    """What a client sends to run one tool (the image travels separately)."""

    tool: str
    params: dict[str, Any] = field(default_factory=dict)
