from __future__ import annotations

from typing import Any

from PIL import Image, ImageEnhance, ImageOps

from engine.base_tool import BaseTool, ToolContext
from engine.schemas.requests import ParamSpec


class AutoEnhanceTool(BaseTool):
    name = "auto_enhance"
    label = "Auto Enhance"
    description = "Fixes contrast automatically, then adjusts color and sharpness."
    params = [
        ParamSpec("contrast_cutoff", "Contrast cutoff %", "slider", 1.0, min=0, max=5, step=0.5),
        ParamSpec("color", "Color", "slider", 1.1, min=0.5, max=2.0, step=0.05),
        ParamSpec("sharpness", "Sharpness", "slider", 1.1, min=0.5, max=2.5, step=0.05),
    ]

    def run(self, image: Image.Image, params: dict[str, Any], ctx: ToolContext) -> Image.Image:
        alpha = image.getchannel("A") if image.mode == "RGBA" else None
        rgb = image.convert("RGB")

        rgb = ImageOps.autocontrast(rgb, cutoff=params["contrast_cutoff"])
        rgb = ImageEnhance.Color(rgb).enhance(params["color"])
        rgb = ImageEnhance.Sharpness(rgb).enhance(params["sharpness"])

        if alpha is not None:
            rgb.putalpha(alpha)
        return rgb
