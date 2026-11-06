from __future__ import annotations

from typing import Any

from PIL import Image, ImageFilter

from engine.base_tool import BaseTool, ToolContext
from engine.schemas.requests import ParamSpec


class BlurTool(BaseTool):
    name = "blur"
    label = "Blur"
    description = "Blur the whole image, or only the background (keeps the person sharp)."
    params = [
        ParamSpec("mode", "Mode", "choice", "whole", choices=["whole", "background"]),
        ParamSpec("strength", "Strength", "slider", 10, min=1, max=50, step=1),
    ]

    def run(self, image: Image.Image, params: dict[str, Any], ctx: ToolContext) -> Image.Image:
        blurred = image.filter(ImageFilter.GaussianBlur(radius=params["strength"]))
        if params["mode"] == "whole":
            return blurred

        # Background mode: sharp where the mask is white (person), blurred elsewhere.
        mask = ctx.models.get("selfie_segmenter").mask(image)
        return Image.composite(image, blurred, mask)
