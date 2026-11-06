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
