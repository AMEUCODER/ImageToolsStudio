from __future__ import annotations

from typing import Any

import numpy as np
from PIL import Image

from engine.base_tool import BaseTool, ToolContext
from engine.schemas.requests import ParamSpec

# Minimum confidence (0-1) a detection needs before it is blurred.
# Higher = fewer false blurs (statues, reflections); lower = catches more faces.
SENSITIVITY = {"Strict": 0.90, "Balanced": 0.80, "Sensitive": 0.65}


class FaceBlurTool(BaseTool):
    name = "face_blur"
    label = "Face Blur"
    description = "Finds every face in the image and blurs it."
    params = [
        ParamSpec("sensitivity", "Detection", "choice", "Balanced", choices=list(SENSITIVITY),
                  help="Strict = fewer false blurs, Sensitive = catches more faces"),
        ParamSpec("strength", "Blur strength", "int", 25, min=1, max=100),
        ParamSpec("padding", "Padding %", "slider", 12, min=0, max=40, step=1,
                  help="Grows each face box to cover hair, ears and chin"),
    ]

    def run(self, image: Image.Image, params: dict[str, Any], ctx: ToolContext) -> Image.Image:
        import cv2                                              # only imported when this tool runs

        detector = ctx.models.get("yunet_face")
        alpha = image.getchannel("A") if image.mode == "RGBA" else None

        # PIL (RGB) -> OpenCV (BGR). ascontiguousarray also makes a writable copy.
        bgr = np.ascontiguousarray(np.asarray(image.convert("RGB"))[:, :, ::-1])
        height, width = bgr.shape[:2]

        kernel = params["strength"] * 2 + 1                     # GaussianBlur needs an odd kernel
        pad = params["padding"] / 100

        for x, y, w, h in detector.detect(bgr, SENSITIVITY[params["sensitivity"]]):
            px, py = int(w * pad), int(h * pad)
            x1, y1 = max(x - px, 0), max(y - py, 0)             # keep the box inside the image
            x2, y2 = min(x + w + px, width), min(y + h + py, height)
            if x2 - x1 < 2 or y2 - y1 < 2:
                continue
            bgr[y1:y2, x1:x2] = cv2.GaussianBlur(bgr[y1:y2, x1:x2], (kernel, kernel), 0)

        out = Image.fromarray(np.ascontiguousarray(bgr[:, :, ::-1]))
        if alpha is not None:
            out.putalpha(alpha)
        return out
