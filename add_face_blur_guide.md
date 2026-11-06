# How to add your Face Blur script as a tool

This guide takes your standalone face-blur script and shows exactly where every part of it goes in the project, which files to create, and what each existing module does when the new tool runs. You can do every step by hand; the code blocks are the real, working files.

---

## 1. The idea in one picture

Your script does three jobs in one file: **find faces**, **blur them**, and **handle files**. The engine keeps those jobs in separate places:

```
YOUR SCRIPT                          WHERE IT GOES IN THE PROJECT
─────────────────────────────        ─────────────────────────────────────────────
load YuNet / Haar, detect_faces  ->  engine/models/adapters/opencv_yunet.py   (the "model")
blur_face (pad box + blur)       ->  engine/tools/face_blur/tool.py           (the "tool")
.onnx path and download URL      ->  engine/models/manifest.json              (the "model list")
sensitivity / ksize / PAD        ->  ParamSpec options in tool.py             (the bottom controls)
read_image / write_image         ->  already exist: engine/image_loader.py and image_exporter.py
unique_path / process_images     ->  not needed for one image (see section 7)
```

Rule of thumb the engine follows: **a tool never imports a model library; it asks the model manager for an adapter.** That is why detection and blurring are two files.

---

## 2. Every part of your script, one by one

| Your script | What it does | Where it went | Changed? |
|---|---|---|---|
| `import os, cv2, numpy` | libraries | adapter imports `cv2` inside `load()`; tool imports `numpy` and `cv2` inside `run()` | Imports moved so the app starts even if OpenCV is missing |
| `IMAGE_EXTS` | allowed file types | not needed | The engine receives one already-open image. Only a folder/batch tool needs it |
| `HERE`, `YUNET_PATH` | where the `.onnx` sits | `manifest.json` (`file`, `url`) plus `ModelManager.weights_dir` (`engine/models/weights/`) | Model is downloaded automatically on first use |
| `CASCADE_PATH` | Haar xml next to the script | adapter uses OpenCV's own copy (`cv2.data.haarcascades`) | No extra file to ship (OpenCV 4.x only) |
| YuNet creation (`FaceDetectorYN.create`) | main detector | `Adapter.load()` | Same arguments |
| Haar creation (`face_cascade`) | fallback detector | `Adapter.load()` | Same idea, checks the file exists first |
| `raise RuntimeError(...)` if no detector | fail early | `ModelUnavailable` raised from `Adapter.load()` | Raised on first use, not at import, so one missing model never stops the whole app |
| `SENSITIVITY` | Strict / Balanced / Sensitive | `SENSITIVITY` dict in `tool.py` and the "Detection" dropdown | Same numbers |
| `DEFAULT_THRESHOLD` | default = Balanced | `default="Balanced"` in the `ParamSpec` | |
| `SMALL_FACE_PX`, `SMALL_FACE_RELAX`, `MAX_DETECT_SIDE` | detection tuning | constants at the top of the adapter | Unchanged |
| `PAD = 0.12` | grow each box 12% | "Padding %" slider (default 12) | Now user-adjustable |
| `detect_faces()` | returns boxes | `Adapter.detect()` | Same logic, plus a lock for thread safety |
| `blur_face(frame, ksize, threshold)` | pad, clamp, blur each box | `FaceBlurTool.run()` | Returns a **new** image; does not return the face count |
| `ksize` | blur kernel size | "Blur strength" slider; kernel = 2 x strength + 1 | Always odd, default 25 gives your 51 |
| `read_image()` | non-ASCII-safe read | `engine/image_loader.py: load_image` (already existed) | Pillow reads Arabic paths fine |
| `write_image()` | non-ASCII-safe write | `engine/image_exporter.py: save_image` (already existed) | |
| `unique_path()` | avoid overwriting | not needed | The Save dialog asks before overwriting |
| `process_images()`, `images_in_folder()` | batch a folder | not included | See section 7 |

Behavior differences worth knowing:
1. Your `blur_face` edits the image in place and returns a count. A tool must return a **new** image, so the face count is not reported yet.
2. Your detector loads when the file is imported. Here it loads the **first time** you press Run on Face Blur.

---

## 3. The files, in the order to create them

```
DesktopApp/
├── requirements.txt                              (edit)     step 1
├── engine/
│   ├── models/
│   │   ├── manifest.json                         (edit)     step 2
│   │   └── adapters/
│   │       ├── base_adapter.py                   (edit)     step 3
│   │       └── opencv_yunet.py                   (new)      step 4
│   └── tools/
│       └── face_blur/
│           ├── __init__.py                       (new, empty)   step 5
│           └── tool.py                           (new)      step 6
└── tests/
    └── test_face_blur.py                         (new, optional)   step 7
```

Nothing else changes. You do not edit the registry, the engine, the sidebar, or the options panel.

### Step 1: `requirements.txt`: add OpenCV

```text
customtkinter>=5.2
pillow>=10.0
numpy>=1.24
requests>=2.31        # only needed for remote mode
mediapipe>=0.10       # optional: Blur "background" mode
opencv-python>=4.8,<5 # Face Blur (4.x includes the Haar fallback file)
pytest>=8.0           # tests
```

The `<5` pin matters: OpenCV 5 no longer ships the Haar cascade file, so the fallback detector would not exist.

### Step 2: `engine/models/manifest.json`: register the model

The manifest is the list of models the model manager knows about. Add the `yunet_face` entry:

```json
{
  "models": {
    "selfie_segmenter": {
      "adapter": "mediapipe_selfie",
      "description": "Person/background mask used by Blur (background mode) and later Background Removal.",
      "requires": ["mediapipe"],
      "file": "selfie_segmenter.tflite",
      "url": "https://storage.googleapis.com/mediapipe-models/image_segmenter/selfie_segmenter/float16/latest/selfie_segmenter.tflite",
      "invert_mask": false
    },
    "yunet_face": {
      "adapter": "opencv_yunet",
      "description": "Face detector used by Face Blur. Falls back to a Haar cascade if the model cannot be downloaded.",
      "requires": ["opencv-python"],
      "file": "face_detection_yunet_2023mar.onnx",
      "url": "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx"
    }
  }
}
```

| Key | Meaning |
|---|---|
| `"yunet_face"` | The name the tool uses: `ctx.models.get("yunet_face")` |
| `adapter` | Which file in `adapters/` handles it (`opencv_yunet.py`) |
| `file` | Filename saved into `engine/models/weights/` |
| `url` | Where to download it from on first use |
| `description`, `requires` | Documentation only |

### Step 3: `engine/models/adapters/base_adapter.py`: add a safe downloader

Add the `download_file` function and the imports above it. (`BaseAdapter` below it was already there.)

```python
"""An adapter wraps ONE model family behind a small, tool-friendly API.

To add a model: create adapters/<name>.py with a class called `Adapter`, then add an
entry to models/manifest.json that points at it. Tools never import model libraries
directly; they call ctx.models.get("<model name>") and use the adapter's methods.
"""
from __future__ import annotations

import urllib.request
from pathlib import Path
from typing import Any


def download_file(url: str, dest: Path) -> None:
    """Download `url` to `dest`. The file only appears once it is complete, so a failed
    or blocked download never leaves a broken model file behind."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    try:
        with urllib.request.urlopen(url, timeout=60) as response, open(tmp, "wb") as out:   # noqa: S310
            while chunk := response.read(1 << 20):
                out.write(chunk)
        tmp.replace(dest)
    finally:
        tmp.unlink(missing_ok=True)


class BaseAdapter:
    def __init__(self, name: str, entry: dict[str, Any], device: str, weights_dir: Path):
        self.name = name
        self.entry = entry
        self.device = device
        self.weights_dir = weights_dir

    def load(self) -> None:
        """Load weights / create the underlying model. Raise ModelUnavailable if impossible."""
        raise NotImplementedError

    def unload(self) -> None:
        """Free memory. Optional."""
```

How `download_file` protects you: it writes to `<name>.part` and only renames it to the real name when the download is **complete**. A blocked or interrupted download never leaves a broken model file that would be loaded later.

### Step 4: `engine/models/adapters/opencv_yunet.py`: the detector (new)

This is your `detect_faces` plus the detector setup.

```python
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
```

What each part does:

| Part | Job |
|---|---|
| Constants `SMALL_FACE_PX`, `SMALL_FACE_RELAX`, `MAX_DETECT_SIDE` | Your tuning values, unchanged |
| `class Adapter(BaseAdapter)` | Required name: the model manager imports this file and creates `Adapter(...)` |
| `load()` | Runs once, the first time the model is requested. Imports OpenCV, downloads the `.onnx` if missing, creates the YuNet detector. If that fails, tries the Haar cascade. If both fail, raises `ModelUnavailable` with the download link |
| `self.backend` | `"yunet"` or `"haar"`, so you can tell which one is active |
| `self._lock` | YuNet stores the input size and threshold on the detector object between calls. The lock stops two simultaneous requests (for example from the backend) from overwriting each other |
| `detect(bgr, threshold)` | Takes an OpenCV image and returns `[(x, y, w, h), ...]`. Large photos are shrunk to 3000 px for detection only, and the boxes are scaled back to full size. Small faces get a gentler confidence bar |

### Step 5: `engine/tools/face_blur/__init__.py`

Create the folder and an **empty** file with this name. It makes the folder a Python package, so the registry can scan it.

### Step 6: `engine/tools/face_blur/tool.py`: the tool (new)

This is your `blur_face`, plus the options for the bottom of the window.

```python
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
```

What each part does:

| Part | Job |
|---|---|
| `class FaceBlurTool(BaseTool)` | The registry finds any `BaseTool` subclass in a `tool.py` |
| `name = "face_blur"` | The id used everywhere: the sidebar, `engine.run("face_blur", ...)`, `/api/tools/face_blur` |
| `label`, `description` | Sidebar text, and the line above the controls |
| `params = [...]` | The three controls at the bottom: a dropdown (`choice`), an integer slider (`int`), and a slider |
| `run(...)` | Receives the image and the **already validated** options |
| `ctx.models.get("yunet_face")` | Asks the model manager for the detector (loads it on first call, reuses it after) |
| `np.asarray(...)[:, :, ::-1]` | PIL stores colors as RGB, OpenCV expects BGR. The `::-1` flips the channel order. `ascontiguousarray` makes a writable copy so the input image is never touched |
| `kernel = strength * 2 + 1` | Gaussian blur needs an odd kernel size |
| The `for` loop | Your `blur_face` body: pad the box, clamp it inside the image, blur just that rectangle |
| `Image.fromarray(...[:, :, ::-1])` | Back to RGB for PIL |
| `alpha` handling | Keeps transparency on PNGs |

### Step 7 (optional): `tests/test_face_blur.py`

Tests the blur logic with a fake detector, so it needs no model download and no real faces.

```python
"""Face Blur. The detector is replaced by a fake so the blur logic is tested exactly;
the real YuNet model is checked separately on a real photo (see README)."""
import numpy as np
import pytest
from PIL import Image

from engine.engine import Engine
from engine.models.adapters import opencv_yunet


class FakeDetector:
    def __init__(self, boxes):
        self.boxes, self.thresholds = boxes, []

    def detect(self, bgr, threshold):
        self.thresholds.append(threshold)
        return self.boxes


@pytest.fixture
def engine():
    return Engine(device="cpu")


@pytest.fixture
def checker():
    """Hard black/white checkerboard: any blur visibly changes it."""
    arr = (np.indices((120, 160)).sum(axis=0) % 2 * 255).astype("uint8")
    return Image.fromarray(np.stack([arr] * 3, axis=-1))


def use_detector(engine, monkeypatch, boxes):
    fake = FakeDetector(boxes)
    monkeypatch.setattr(engine.models, "get", lambda name: fake)
    return fake


def region(img, box):
    return np.asarray(img.convert("RGB").crop(box)).astype(int)


def test_only_the_face_box_is_blurred(engine, checker, monkeypatch):
    use_detector(engine, monkeypatch, [(40, 30, 50, 50)])
    out = engine.run("face_blur", checker, {"padding": 0, "strength": 10})
    assert out.size == checker.size
    assert region(out, (40, 30, 90, 80)).std() < region(checker, (40, 30, 90, 80)).std() / 2
    assert (region(out, (0, 0, 30, 20)) == region(checker, (0, 0, 30, 20))).all()   # outside: untouched


def test_padding_grows_the_blurred_area(engine, checker, monkeypatch):
    use_detector(engine, monkeypatch, [(60, 40, 40, 40)])
    tight = engine.run("face_blur", checker, {"padding": 0, "strength": 10})
    padded = engine.run("face_blur", checker, {"padding": 40, "strength": 10})
    ring = (56, 36, 60, 40)                                  # just outside the face box
    assert region(tight, ring).std() > region(padded, ring).std()


def test_box_touching_the_edge_does_not_crash(engine, checker, monkeypatch):
    use_detector(engine, monkeypatch, [(-10, -10, 40, 40), (140, 100, 60, 60), (5, 5, 1, 1)])
    out = engine.run("face_blur", checker, {"padding": 40})
    assert out.size == checker.size


def test_no_faces_leaves_image_identical(engine, checker, monkeypatch):
    use_detector(engine, monkeypatch, [])
    assert (region(engine.run("face_blur", checker), (0, 0, 160, 120)) == region(checker, (0, 0, 160, 120))).all()


def test_sensitivity_maps_to_thresholds(engine, checker, monkeypatch):
    fake = use_detector(engine, monkeypatch, [])
    for name in ("Strict", "Balanced", "Sensitive"):
        engine.run("face_blur", checker, {"sensitivity": name})
    assert fake.thresholds == [0.90, 0.80, 0.65]


def test_input_unchanged_and_alpha_kept(engine, monkeypatch):
    use_detector(engine, monkeypatch, [(10, 10, 30, 30)])
    rgba = Image.fromarray(np.random.default_rng(0).integers(0, 255, (60, 60, 4), dtype="uint8"))
    rgba.putalpha(Image.new("L", rgba.size, 99))
    before = rgba.copy()
    out = engine.run("face_blur", rgba)
    assert out.mode == "RGBA" and out.getpixel((0, 0))[3] == 99
    assert (np.asarray(rgba) == np.asarray(before)).all()


def _offline(monkeypatch):
    def blocked(url, dest):
        raise OSError("blocked")

    monkeypatch.setattr(opencv_yunet, "download_file", blocked)


def _haar_file_exists():
    import os

    import cv2
    return os.path.exists(os.path.join(getattr(getattr(cv2, "data", None), "haarcascades", ""),
                                       "haarcascade_frontalface_default.xml"))


@pytest.mark.skipif(not _haar_file_exists(), reason="this OpenCV build has no Haar cascade file (OpenCV 5)")
def test_falls_back_to_haar_when_model_cannot_download(tmp_path, checker, monkeypatch):
    _offline(monkeypatch)
    isolated = Engine(weights_dir=tmp_path, device="cpu")                     # empty weights folder
    out = isolated.run("face_blur", checker)                                  # a checkerboard has no faces
    assert out.size == checker.size
    assert isolated.models.get("yunet_face").backend == "haar"
    assert not list(tmp_path.glob("*.part"))                                  # no half-downloaded files


@pytest.mark.skipif(_haar_file_exists(), reason="a Haar fallback exists in this OpenCV build")
def test_clear_error_when_no_detector_at_all(tmp_path, checker, monkeypatch):
    from engine.errors import ModelUnavailable
    _offline(monkeypatch)
    isolated = Engine(weights_dir=tmp_path, device="cpu")
    with pytest.raises(ModelUnavailable, match="face_detection_yunet_2023mar.onnx"):
        isolated.run("face_blur", checker)
    assert not list(tmp_path.glob("*.part"))
```

Run everything with `pytest` from `DesktopApp/`.

---

## 4. What happens when you click Face Blur and press Run

Every existing module that touches the new tool, in order:

| # | Module | What it does with Face Blur |
|---|---|---|
| 1 | `engine/tool_registry.py` | At startup, scans `engine/tools/`, imports `face_blur/tool.py`, creates `FaceBlurTool()` and stores it under `"face_blur"` |
| 2 | `runners/local_runner.py` | `describe_tools()` returns the tool's `name`, `label`, `description` and `params` |
| 3 | `run_desktop.py` | Passes that list to `MainWindow` |
| 4 | `interface/sidebar.py` | Adds a "Face Blur" button |
| 5 | `interface/main_window.py` | On click: remembers `current_tool = "face_blur"`, tells the workspace to show it |
| 6 | `interface/workspace.py` | Shows the description and asks the options panel to build the controls |
| 7 | `interface/components/params_panel.py` | Builds a dropdown (Detection), a slider (Blur strength), a slider (Padding %) from the `ParamSpec` list |
| 8 | `controllers/editor_controller.py` | On **Run**: starts a worker thread and calls `runner.run("face_blur", image, params)` |
| 9 | `runners/local_runner.py` | Calls `Engine.run(...)` (or `RemoteRunner` sends it to the backend, which calls the same function) |
| 10 | `engine/engine.py` | Looks up the tool in the registry |
| 11 | `engine/schemas/validation.py` | Fills defaults, clamps `strength` to 1-100, rejects an invalid `sensitivity` |
| 12 | `engine/tools/face_blur/tool.py` | `run()` executes |
| 13 | `engine/model_manager.py` | `get("yunet_face")`: reads `manifest.json`, imports `opencv_yunet.py`, calls `Adapter.load()`, caches the adapter |
| 14 | `engine/models/adapters/opencv_yunet.py` | Downloads the model if needed, then `detect()` returns the boxes |
| 15 | back in `tool.py` | Blurs each box, returns a new image |
| 16 | `controllers/editor_controller.py` | Saves the previous image for Undo, shows the result on the canvas |

---

## 5. Checklist: it did not appear, or it fails

| Symptom | Cause and fix |
|---|---|
| No "Face Blur" button | Missing `__init__.py` in `face_blur/`, the file is not named `tool.py`, or the class does not extend `BaseTool` |
| Button missing and the app still starts | The file has an error. Check `engine.registry.failed`: it holds the exact import error |
| "Face blur needs OpenCV" | `pip install "opencv-python>=4.8,<5"` |
| "No face detector available" | The model download was blocked. Download the `.onnx` from the `url` in `manifest.json` and put it in `engine/models/weights/` with the same filename |
| Blurs nothing | Try "Sensitive". Faces smaller than about 24 px already get a gentler bar |
| Blurs statues or reflections | Switch to "Strict" |
| Weird colors in the result | The RGB/BGR flip (`[:, :, ::-1]`) was removed or applied twice |
| `ParamError: Unknown parameter` | A name in `params` and the name used in `run()` do not match |

---

## 6. The pattern for any other tool

1. Model needed? Add an entry to `manifest.json` and an adapter file with `class Adapter(BaseAdapter)` and a `load()`.
2. Create `engine/tools/<name>/__init__.py` (empty) and `tool.py` with a `BaseTool` subclass.
3. Declare the options as `ParamSpec` entries; they become the bottom controls.
4. Write `run(image, params, ctx)` that returns a **new** image.

---

## 7. Batch processing (your `process_images` and `images_in_folder`)

These were left out on purpose. A tool receives one image at a time, and the window edits one image at a time. A folder batch is a different feature, with two natural homes:

- **In the controller:** a "Run on folder" button that loops over files, calls `runner.run(...)` for each, and saves with `save_image` to an output folder. `images_in_folder` and `unique_path` would live next to it (for example in `engine/image_loader.py` and `engine/image_exporter.py`).
- **In the backend:** a job that takes several uploads and reports progress through `GET /api/jobs/{id}`.

Your `progress(i, total, filename, faces, out_path, error)` callback maps directly onto either. If you want, I can show you how to add it, but I won't change anything until you ask.
