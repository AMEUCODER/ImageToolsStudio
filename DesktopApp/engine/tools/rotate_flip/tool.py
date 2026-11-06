from __future__ import annotations

from typing import Any

from PIL import Image, ImageOps

from engine.base_tool import BaseTool, ToolContext
from engine.schemas.requests import ParamSpec


class RotateFlipTool(BaseTool):
    name = "rotate_flip"
    label = "Rotate / Flip"
    description = "Turn by 90 degrees, straighten by a few degrees, and mirror."
    params = [
        ParamSpec("turn", "Turn", "choice", "0", choices=["0", "90", "180", "270"], help="Degrees, clockwise"),
        ParamSpec("straighten", "Straighten", "slider", 0, min=-45, max=45, step=0.5),
        ParamSpec("flip_h", "Mirror left/right", "bool", False),
        ParamSpec("flip_v", "Flip upside down", "bool", False),
    ]

    def run(self, image: Image.Image, params: dict[str, Any], ctx: ToolContext) -> Image.Image:
        out = image.copy()
        if params["flip_h"]:
            out = ImageOps.mirror(out)
        if params["flip_v"]:
            out = ImageOps.flip(out)

        turn = int(params["turn"])
        if turn:
            out = out.rotate(-turn, expand=True)          # PIL rotates counter-clockwise

        if params["straighten"]:
            fill = (0, 0, 0, 0) if out.mode == "RGBA" else (255, 255, 255)
            out = out.rotate(-params["straighten"], expand=True, resample=Image.BICUBIC, fillcolor=fill)
        return out
