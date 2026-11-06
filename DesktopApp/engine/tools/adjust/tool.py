from __future__ import annotations

from typing import Any

from PIL import Image, ImageEnhance

from engine.base_tool import BaseTool, ToolContext
from engine.schemas.requests import ParamSpec


class AdjustTool(BaseTool):
    name = "adjust"
    label = "Adjust"
    description = "Manual brightness, contrast, saturation and color temperature."
    params = [
        ParamSpec("brightness", "Brightness", "slider", 1.0, min=0.2, max=2.0, step=0.05),
        ParamSpec("contrast", "Contrast", "slider", 1.0, min=0.2, max=2.0, step=0.05),
        ParamSpec("saturation", "Saturation", "slider", 1.0, min=0.0, max=2.0, step=0.05, help="0 = black and white"),
        ParamSpec("warmth", "Warmth", "slider", 0, min=-50, max=50, step=1, help="negative = cooler, positive = warmer"),
    ]

    def run(self, image: Image.Image, params: dict[str, Any], ctx: ToolContext) -> Image.Image:
        alpha = image.getchannel("A") if image.mode == "RGBA" else None
        out = image.convert("RGB")

        out = ImageEnhance.Brightness(out).enhance(params["brightness"])
        out = ImageEnhance.Contrast(out).enhance(params["contrast"])
        out = ImageEnhance.Color(out).enhance(params["saturation"])

        warmth = params["warmth"]
        if warmth:
            red, green, blue = out.split()
            red = red.point(lambda v: max(0, min(255, v + warmth)))
            blue = blue.point(lambda v: max(0, min(255, v - warmth)))
            out = Image.merge("RGB", (red, green, blue))

        if alpha is not None:
            out.putalpha(alpha)
        return out
