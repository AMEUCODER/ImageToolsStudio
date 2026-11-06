"""MediaPipe selfie segmentation: returns a soft person mask (white = person).

Uses the MediaPipe Tasks API (the old `mp.solutions` API was removed in recent
releases). The small .tflite model is downloaded once into engine/models/weights/.
"""
from __future__ import annotations

import urllib.request
from pathlib import Path

from PIL import Image

from engine.errors import ModelUnavailable
from engine.models.adapters.base_adapter import BaseAdapter


def _download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    urllib.request.urlretrieve(url, tmp)          # noqa: S310 - fixed URL from manifest.json
    tmp.replace(dest)                             # never leave a half-downloaded file behind


class Adapter(BaseAdapter):
    def load(self) -> None:
        try:
            import mediapipe as mp
            from mediapipe.tasks import python as mp_python
            from mediapipe.tasks.python import vision
        except ImportError as exc:
            raise ModelUnavailable("This option needs mediapipe: pip install mediapipe") from exc

        weights = self.weights_dir / self.entry["file"]
        if not weights.exists():
            try:
                _download(self.entry["url"], weights)
            except Exception as exc:              # noqa: BLE001 - offline, blocked, disk full...
                raise ModelUnavailable(
                    f"Could not download the segmentation model ({exc}). "
                    f"Download {self.entry['url']} and save it as {weights}"
                ) from exc

        self._mp = mp
        options = vision.ImageSegmenterOptions(
            base_options=mp_python.BaseOptions(model_asset_path=str(weights)),
            output_confidence_masks=True,
            output_category_mask=False,
        )
        self._segmenter = vision.ImageSegmenter.create_from_options(options)

    def mask(self, image: Image.Image) -> Image.Image:
        import numpy as np

        rgb = np.ascontiguousarray(np.asarray(image.convert("RGB")))
        mp_image = self._mp.Image(image_format=self._mp.ImageFormat.SRGB, data=rgb)
        result = self._segmenter.segment(mp_image)

        confidence = result.confidence_masks[-1].numpy_view().squeeze()   # 0..1, person = high
        if self.entry.get("invert_mask"):
            confidence = 1.0 - confidence
        mask = (confidence * 255).clip(0, 255).astype("uint8")
        return Image.fromarray(mask, mode="L")

    def unload(self) -> None:
        self._segmenter.close()
