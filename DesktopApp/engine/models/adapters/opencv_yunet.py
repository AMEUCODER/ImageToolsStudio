"""Face detection: YuNet (built into OpenCV) with a Haar-cascade fallback.

Ported from the standalone face-blur script. It only DETECTS faces; the blurring is
done by the tool in engine/tools/face_blur/. Boxes are (x, y, w, h) in the pixel
coordinates of the image that was passed in.
"""
from __future__ import annotations

import os
import threading

from engine.errors import ModelUnavailable
from engine.models.adapters.base_adapter import BaseAdapter, download_file

SMALL_FACE_PX = 24        # tiny/distant faces always score lower, so they get a gentler bar
SMALL_FACE_RELAX = 0.15
MAX_DETECT_SIDE = 3000    # only huge photos are shrunk for detection (keeps small faces findable)


class Adapter(BaseAdapter):
    def load(self) -> None:
        try:
            import cv2
        except ImportError as exc:
            raise ModelUnavailable('Face blur needs OpenCV: pip install "opencv-python>=4.8"') from exc
        self._cv2 = cv2
        self._lock = threading.Lock()          # YuNet keeps per-call state (input size, threshold)
        self._yunet = None
        self._haar = None
        self.backend = ""

        weights = self.weights_dir / self.entry["file"]
        if hasattr(cv2, "FaceDetectorYN"):
            if not weights.exists():
                try:
                    download_file(self.entry["url"], weights)
                except Exception:              # noqa: BLE001 - offline/blocked: fall back to Haar below
                    pass
            if weights.exists():
                # args: model, config, input size (reset per image), score, NMS, top_k
                self._yunet = cv2.FaceDetectorYN.create(str(weights), "", (320, 320), 0.6, 0.3, 5000)
                self.backend = "yunet"

        if self._yunet is None:                # fallback: older, misses small or turned faces
            # OpenCV 4.x ships this file; OpenCV 5 does not, hence the pin in requirements.txt
            cascade_dir = getattr(getattr(cv2, "data", None), "haarcascades", "")
            cascade_file = os.path.join(cascade_dir, "haarcascade_frontalface_default.xml")
            cascade = cv2.CascadeClassifier(cascade_file) if os.path.exists(cascade_file) else None
            if cascade is None or cascade.empty():
                raise ModelUnavailable(
                    "No face detector available. Download "
                    f"{self.entry['url']} and save it as {weights}  "
                    '(or install OpenCV 4.x, which includes a built-in fallback: pip install "opencv-python>=4.8,<5")'
                )
            self._haar = cascade
            self.backend = "haar"

    def detect(self, bgr, threshold: float = 0.8) -> list[tuple[int, int, int, int]]:
        """Return face boxes. `bgr` is an OpenCV (BGR) uint8 array; `threshold` is 0 to 1."""
        cv2 = self._cv2
        height, width = bgr.shape[:2]

        if self._yunet is not None:
            scale = min(1.0, MAX_DETECT_SIDE / max(height, width))
            img = cv2.resize(bgr, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA) if scale < 1 else bgr
            low = max(0.3, threshold - SMALL_FACE_RELAX)
            with self._lock:
                self._yunet.setInputSize((img.shape[1], img.shape[0]))
                self._yunet.setScoreThreshold(low)     # collect candidates, then apply the size-aware bar
                _, found = self._yunet.detect(img)
            if found is None:
                return []
            boxes = []
            for f in found:
                x, y, w, h = (int(round(v / scale)) for v in f[:4])
                need = low if max(w, h) < SMALL_FACE_PX else threshold
                if float(f[14]) >= need:
                    boxes.append((x, y, w, h))
            return boxes

        gray = cv2.equalizeHist(cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY))
        with self._lock:
            faces = self._haar.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(20, 20))
        return [tuple(int(v) for v in f) for f in faces]
