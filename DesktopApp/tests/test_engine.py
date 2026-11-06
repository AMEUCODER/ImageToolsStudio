import pytest
from PIL import Image, ImageChops

from engine.engine import Engine
from engine.errors import ModelUnavailable, ParamError, ToolNotFound
from engine.schemas.responses import ToolInfo
from runners.base_runner import RunnerError
from runners.local_runner import LocalRunner


@pytest.fixture(scope="module")
def engine():
    return Engine(device="cpu")


@pytest.fixture
def image():
    img = Image.new("RGB", (64, 48), "white")
    for x in range(32):
        for y in range(48):
            img.putpixel((x, y), (200, 30, 30))
    return img


def same(a, b):
    return ImageChops.difference(a.convert("RGB"), b.convert("RGB")).getbbox() is None


def test_registry_discovers_tools(engine):
    assert {"blur", "auto_enhance"} <= set(engine.list_tools())
    assert engine.registry.failed == {}


def test_blur_whole_changes_image_not_input(engine, image):
    before = image.copy()
    out = engine.run("blur", image, {"mode": "whole", "strength": 5})
    assert out.size == image.size
    assert not same(out, image)
    assert same(image, before)                    # input is never modified


def test_defaults_and_clamping(engine, image):
    engine.run("blur", image)                     # all defaults
    engine.run("blur", image, {"strength": 9999}) # clamped to max, no error


def test_bad_params(engine, image):
    with pytest.raises(ParamError):
        engine.run("blur", image, {"mode": "sideways"})
    with pytest.raises(ParamError):
        engine.run("blur", image, {"nope": 1})
    with pytest.raises(ParamError):
        engine.run("blur", image, {"strength": "abc"})


def test_unknown_tool(engine, image):
    with pytest.raises(ToolNotFound):
        engine.run("teleport", image)


def test_auto_enhance_keeps_alpha(engine):
    rgba = Image.new("RGBA", (10, 10), (100, 100, 100, 128))
    out = engine.run("auto_enhance", rgba)
    assert out.mode == "RGBA" and out.getpixel((0, 0))[3] == 128


def test_pipeline(engine, image):
    out = engine.pipeline().add("auto_enhance").add("blur", {"strength": 3}).run(image)
    assert out.size == image.size


def test_background_blur_reports_unavailable_model_cleanly(tmp_path, image, monkeypatch):
    """No weights + no download possible -> a clear ModelUnavailable, not a crash."""
    from engine.models.adapters import mediapipe_selfie

    def offline(url, dest):
        raise OSError("offline")

    monkeypatch.setattr(mediapipe_selfie, "_download", offline)
    isolated = Engine(weights_dir=tmp_path, device="cpu")     # empty weights folder
    with pytest.raises(ModelUnavailable):
        isolated.run("blur", image, {"mode": "background"})


def test_tool_info_roundtrip(engine):
    for info in engine.describe_tools():
        assert ToolInfo.from_dict(info.to_dict()) == info


def test_local_runner(engine, image):
    runner = LocalRunner(engine)
    assert "blur" in runner.list_tools()
    runner.run("blur", image, {})
    with pytest.raises(RunnerError):
        runner.run("teleport", image)


# ---- new tools and option kinds -------------------------------------------
def test_new_tools_are_discovered(engine):
    assert {"crop", "rotate_flip", "adjust", "watermark"} <= set(engine.list_tools())
    assert engine.registry.failed == {}


def test_crop_ratio_zoom_and_offsets(engine):
    img = Image.new("RGB", (400, 200), "white")
    assert engine.run("crop", img, {"aspect": "1:1"}).size == (200, 200)
    assert engine.run("crop", img, {"aspect": "1:1", "zoom": 2}).size == (100, 100)
    assert engine.run("crop", img).size == (400, 200)                       # original = no change
    for ox in (-100, 100):                                                   # never leaves the image
        engine.run("crop", img, {"aspect": "16:9", "zoom": 3, "offset_x": ox, "offset_y": ox})


def test_crop_offsets_move_the_window(engine):
    img = Image.new("RGB", (400, 200), "white")
    for x in range(200):
        for y in range(200):
            img.putpixel((x, y), (255, 0, 0))                                # left half red
    left = engine.run("crop", img, {"aspect": "1:1", "offset_x": -100})
    right = engine.run("crop", img, {"aspect": "1:1", "offset_x": 100})
    assert left.getpixel((10, 10)) == (255, 0, 0) and right.getpixel((10, 10)) == (255, 255, 255)


def test_rotate_flip(engine):
    img = Image.new("RGB", (60, 30), "white")
    assert engine.run("rotate_flip", img, {"turn": "90"}).size == (30, 60)
    assert engine.run("rotate_flip", img, {"turn": "180"}).size == (60, 30)
    assert engine.run("rotate_flip", img, {"straighten": 10}).size[0] > 60   # canvas grows to fit
    marked = Image.new("RGB", (4, 2), "white")
    marked.putpixel((0, 0), (255, 0, 0))
    assert engine.run("rotate_flip", marked, {"flip_h": True}).getpixel((3, 0)) == (255, 0, 0)


def test_adjust_values(engine):
    gray = Image.new("RGB", (8, 8), (100, 100, 100))
    assert engine.run("adjust", gray, {"brightness": 2.0}).getpixel((0, 0))[0] > 100
    warm = engine.run("adjust", gray, {"warmth": 30}).getpixel((0, 0))
    assert warm[0] > warm[2]                                                 # red up, blue down
    bw = engine.run("adjust", Image.new("RGB", (4, 4), (200, 50, 50)), {"saturation": 0}).getpixel((0, 0))
    assert bw[0] == bw[1] == bw[2]
    rgba = Image.new("RGBA", (4, 4), (100, 100, 100, 77))
    assert engine.run("adjust", rgba).getpixel((0, 0))[3] == 77


def test_watermark_draws_only_where_asked(engine):
    img = Image.new("RGB", (300, 200), (0, 0, 0))
    out = engine.run("watermark", img, {"text": "HELLO", "color": "#ff0000", "size": 15, "opacity": 1.0,
                                        "position": "bottom right"})
    assert out.size == img.size and out.mode == "RGB"
    assert out.getpixel((5, 5)) == (0, 0, 0)                                 # far corner untouched
    assert out.crop((150, 100, 300, 200)).getextrema()[0][1] > 0            # red text in bottom right
    assert same(engine.run("watermark", img, {"text": "   "}), img)          # blank text = no change


def test_text_and_color_validation(engine):
    img = Image.new("RGB", (50, 50), "white")
    with pytest.raises(ParamError):
        engine.run("watermark", img, {"color": "red"})
    with pytest.raises(ParamError):
        engine.run("watermark", img, {"color": "#12345"})
    engine.run("watermark", img, {"text": "x" * 500, "color": "#ABCDEF"})    # long text is trimmed, case ok
