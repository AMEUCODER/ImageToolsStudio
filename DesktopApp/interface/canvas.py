"""Shows the current image, scaled to fit, and re-fits when the window is resized."""
from __future__ import annotations

import customtkinter as ctk
from PIL import Image


class Canvas(ctk.CTkFrame):
    PADDING = 16

    def __init__(self, master):
        super().__init__(master, fg_color=("gray88", "gray14"))
        self._image: Image.Image | None = None
        self._resize_job = None

        self._label = ctk.CTkLabel(self, text="Open an image to start\n(Ctrl+O)", text_color="gray")
        self._label.place(relx=0.5, rely=0.5, anchor="center")
        self.bind("<Configure>", self._on_resize)

    def show(self, image: Image.Image) -> None:
        self._image = image
        self._render()

    def _on_resize(self, _event) -> None:
        if self._image is None:
            return
        if self._resize_job is not None:
            self.after_cancel(self._resize_job)
        self._resize_job = self.after(80, self._render)   # wait until resizing pauses

    def _render(self) -> None:
        self._resize_job = None
        if self._image is None:
            return
        max_w = max(self.winfo_width() - 2 * self.PADDING, 50)
        max_h = max(self.winfo_height() - 2 * self.PADDING, 50)
        scale = min(max_w / self._image.width, max_h / self._image.height, 1.0)
        size = (max(1, int(self._image.width * scale)), max(1, int(self._image.height * scale)))

        preview = self._image.resize(size, Image.LANCZOS)   # display only; full image is kept
        photo = ctk.CTkImage(light_image=preview, dark_image=preview, size=size)
        self._label.configure(image=photo, text="")
        self._label.image = photo                           # keep a reference or it goes blank
