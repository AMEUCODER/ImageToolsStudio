from __future__ import annotations

from typing import Any

from PIL import Image, ImageDraw, ImageFont

from engine.base_tool import BaseTool, ToolContext
from engine.schemas.requests import ParamSpec

_POSITIONS = ["bottom right", "bottom left", "top right", "top left", "center"]


class WatermarkTool(BaseTool):
    name = "watermark"
    label = "Text Watermark"
    description = "Stamp a line of text on the image."
    params = [
        ParamSpec("text", "Text", "text", "My Studio", max=60),
        ParamSpec("color", "Color", "color", "#ffffff"),
        ParamSpec("size", "Size %", "slider", 6, min=2, max=25, step=1, help="Height as % of image width"),
        ParamSpec("opacity", "Opacity", "slider", 0.7, min=0.1, max=1.0, step=0.05),
        ParamSpec("position", "Position", "choice", "bottom right", choices=_POSITIONS),
    ]

    def run(self, image: Image.Image, params: dict[str, Any], ctx: ToolContext) -> Image.Image:
        text = params["text"].strip()
        if not text:
            return image.copy()

        base = image.convert("RGBA")
        font = ImageFont.load_default(size=max(10, int(base.width * params["size"] / 100)))
        overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
        text_w, text_h = right - left, bottom - top
        margin = max(8, base.width // 40)
        positions = {
            "bottom right": (base.width - text_w - margin, base.height - text_h - margin),
            "bottom left": (margin, base.height - text_h - margin),
            "top right": (base.width - text_w - margin, margin),
            "top left": (margin, margin),
            "center": ((base.width - text_w) // 2, (base.height - text_h) // 2),
        }
        x, y = positions[params["position"]]

        red, green, blue = (int(params["color"][i:i + 2], 16) for i in (1, 3, 5))
        draw.text((x - left, y - top), text, font=font, fill=(red, green, blue, int(255 * params["opacity"])))

        result = Image.alpha_composite(base, overlay)
        return result if image.mode == "RGBA" else result.convert("RGB")
