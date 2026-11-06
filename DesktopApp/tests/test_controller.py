"""Tests the controller without a window: a fake view stands in for MainWindow."""
import time

from PIL import Image

from controllers.editor_controller import EditorController
from engine.engine import Engine
from runners.local_runner import LocalRunner


class FakeView:
    def __init__(self):
        self.events = []
        self._jobs = []

    def after(self, _ms, fn):
        self._jobs.append(fn)

    def pump(self, timeout=5):
        """Run scheduled callbacks like Tk's event loop would."""
        end = time.time() + timeout
        while self._jobs and time.time() < end:
            self._jobs.pop(0)()
            time.sleep(0.01)

    def show_image(self, image): self.events.append(("image", image.size))
    def set_busy(self, busy, tool=None): self.events.append(("busy", busy))
    def set_can_undo(self, v): self.events.append(("undo", v))
    def set_status(self, text): self.events.append(("status", text))
    def show_error(self, msg): self.events.append(("error", msg))


def make(tmp_path):
    path = tmp_path / "in.png"
    Image.new("RGB", (40, 30), "red").save(path)
    view = FakeView()
    controller = EditorController(LocalRunner(Engine(device="cpu")), view)
    controller.open_image(str(path))
    return controller, view


def test_run_undo_reset(tmp_path):
    controller, view = make(tmp_path)
    controller.run_tool("blur", {"strength": 3})
    view.pump()
    assert ("busy", True) in view.events and ("busy", False) in view.events
    assert ("undo", True) in view.events

    controller.undo()
    assert controller.image is controller.original
    controller.run_tool("auto_enhance", {})
    view.pump()
    controller.reset()
    assert controller.image is controller.original


def test_error_goes_to_view(tmp_path):
    controller, view = make(tmp_path)
    controller.run_tool("teleport", {})
    view.pump()
    assert any(e[0] == "error" and "teleport" in e[1] for e in view.events)
    assert ("busy", False) in view.events         # UI is re-enabled after a failure


def test_run_without_image():
    view = FakeView()
    controller = EditorController(LocalRunner(Engine(device="cpu")), view)
    controller.run_tool("blur", {})
    assert view.events == [("error", "Open an image first")]


def test_save(tmp_path):
    controller, _ = make(tmp_path)
    out = tmp_path / "sub" / "out.jpg"
    controller.save_image(str(out))
    assert out.exists()
