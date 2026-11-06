from __future__ import annotations

from typing import Any

from PIL import Image

from engine.base_tool import BaseTool, ToolContext
from engine.schemas.requests import ParamSpec

_RATIOS = {"1:1": 1.0, "4:3": 4 / 3, "3:2": 3 / 2, "16:9": 16 / 9, "9:16": 9 / 16, "3:4": 3 / 4}


class CropTool(BaseTool):
    name = "crop"
    label = "Crop"
    description = "Crop to an aspect ratio. Zoom in and move the crop window with the offsets."
    params = [
        ParamSpec("aspect", "Aspect ratio", "choice", "original", choices=["original", *_RATIOS]),
        ParamSpec("zoom", "Zoom", "slider", 1.0, min=1.0, max=4.0, step=0.1, help="1 = widest possible crop"),
        ParamSpec("offset_x", "Move left/right", "slider", 0, min=-100, max=100, step=1),
        ParamSpec("offset_y", "Move up/down", "slider", 0, min=-100, max=100, step=1),
    ]

    def run(self, image: Image.Image, params: dict[str, Any], ctx: ToolContext) -> Image.Image:
        width, height = image.size
        ratio = width / height if params["aspect"] == "original" else _RATIOS[params["aspect"]]

        # largest box with this ratio that fits inside the image
        box_w = min(width, height * ratio)
        box_h = box_w / ratio
        box_w, box_h = box_w / params["zoom"], box_h / params["zoom"]

        # offsets move the box inside the free space (-100 = far left/top, +100 = far right/bottom)
        free_x, free_y = width - box_w, height - box_h
        left = free_x / 2 + params["offset_x"] / 100 * free_x / 2
        top = free_y / 2 + params["offset_y"] / 100 * free_y / 2

        box = (round(left), round(top), round(left + box_w), round(top + box_h))
        return image.crop(box)
