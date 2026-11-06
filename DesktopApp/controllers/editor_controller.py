"""Connects the window to a runner. Holds the image and its undo history.

Rule: tools never run on the UI thread. The work goes to a worker thread, which
puts its result in a queue; the UI thread polls that queue with after().
Tkinter widgets are not thread-safe, so only the UI thread ever touches them.
"""
from __future__ import annotations

import queue
import threading
from pathlib import Path
from typing import Any

from PIL import Image

from engine.image_exporter import save_image
from engine.image_loader import load_image

HISTORY_LIMIT = 20
POLL_MS = 50


class EditorController:
    def __init__(self, runner, view):
        self.runner = runner
        self.view = view
        self.original: Image.Image | None = None
        self.image: Image.Image | None = None
        self._history: list[Image.Image] = []
        self._results: queue.Queue = queue.Queue()
        self._busy = False

    # ---- files -----------------------------------------------------------
    def open_image(self, path: str) -> None:
        try:
            image = load_image(path)
        except Exception as exc:                      # noqa: BLE001 - show any read error
            self.view.show_error(f"Could not open image: {exc}")
            return
        self.original = image
        self.image = image
        self._history.clear()
        self.view.show_image(image)
        self.view.set_can_undo(False)
        self.view.set_status(f"Opened {Path(path).name}  ({image.width}x{image.height})")

    def save_image(self, path: str) -> None:
        if self.image is None:
            self.view.show_error("Nothing to save yet")
            return
        try:
            save_image(self.image, path)
        except Exception as exc:                      # noqa: BLE001
            self.view.show_error(f"Could not save image: {exc}")
            return
        self.view.set_status(f"Saved {path}")

    # ---- running tools ---------------------------------------------------
    def run_tool(self, tool: str, params: dict[str, Any]) -> None:
        if self._busy:
            return
        if self.image is None:
            self.view.show_error("Open an image first")
            return

        self._busy = True
        self.view.set_busy(True, tool)
        source = self.image

        def worker() -> None:
            try:
                self._results.put(("ok", self.runner.run(tool, source, params)))
            except Exception as exc:                  # noqa: BLE001 - forward to the UI thread
                self._results.put(("error", str(exc) or exc.__class__.__name__))

        threading.Thread(target=worker, daemon=True).start()
        self.view.after(POLL_MS, self._poll)

    def _poll(self) -> None:
        try:
            status, payload = self._results.get_nowait()
        except queue.Empty:
            self.view.after(POLL_MS, self._poll)
            return

        self._busy = False
        self.view.set_busy(False)
        if status == "ok":
            self._history.append(self.image)
            del self._history[:-HISTORY_LIMIT]
            self.image = payload
            self.view.show_image(payload)
            self.view.set_can_undo(True)
        else:
            self.view.show_error(payload)

    # ---- history ---------------------------------------------------------
    def undo(self) -> None:
        if self._busy or not self._history:
            return
        self.image = self._history.pop()
        self.view.show_image(self.image)
        self.view.set_can_undo(bool(self._history))

    def reset(self) -> None:
        if self._busy or self.original is None:
            return
        self._history.clear()
        self.image = self.original
        self.view.show_image(self.image)
        self.view.set_can_undo(False)
        self.view.set_status("Back to the original image")
