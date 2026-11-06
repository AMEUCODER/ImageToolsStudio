"""Turns raw client parameters into clean, typed, in-range values."""
from __future__ import annotations

import re
import re
from typing import Any, Iterable

from engine.errors import ParamError
from engine.schemas.requests import ParamSpec


_HEX_COLOR = re.compile(r"#[0-9a-fA-F]{6}")


def validate_params(specs: Iterable[ParamSpec], params: dict[str, Any] | None) -> dict[str, Any]:
    """Fill defaults, coerce types, clamp numbers, reject unknown names/choices."""
    specs = list(specs)
    params = dict(params or {})

    unknown = set(params) - {s.name for s in specs}
    if unknown:
        raise ParamError(f"Unknown parameter(s): {', '.join(sorted(unknown))}")

    return {spec.name: _coerce(spec, params.get(spec.name, spec.default)) for spec in specs}


def _coerce(spec: ParamSpec, value: Any) -> Any:
    if spec.kind == "bool":
        if isinstance(value, str):
            return value.strip().lower() in ("1", "true", "yes", "on")
        return bool(value)

    if spec.kind == "text":
        limit = int(spec.max) if spec.max else 200
        return str(value)[:limit]

    if spec.kind == "color":
        value = str(value).strip()
        if not re.fullmatch(r"#[0-9a-fA-F]{6}", value):
            raise ParamError(f"'{spec.label}' must be a color like #ff8800, got {value!r}")
        return value.lower()

    if spec.kind == "choice":
        value = str(value)
        if value not in spec.choices:
            raise ParamError(f"'{spec.label}' must be one of {spec.choices}, got '{value}'")
        return value

    if spec.kind in ("slider", "int"):
        try:
            number = float(value)
        except (TypeError, ValueError):
            raise ParamError(f"'{spec.label}' must be a number, got {value!r}") from None
        if spec.min is not None:
            number = max(spec.min, number)
        if spec.max is not None:
            number = min(spec.max, number)
        return int(round(number)) if spec.kind == "int" else number

    if spec.kind == "text":
        return str(value)[: int(spec.max or 200)]

    if spec.kind == "color":
        value = str(value).strip()
        if not _HEX_COLOR.fullmatch(value):
            raise ParamError(f"'{spec.label}' must be a hex color like #ff8800, got {value!r}")
        return value.lower()

    raise ParamError(f"Unsupported parameter kind '{spec.kind}' for '{spec.name}'")
