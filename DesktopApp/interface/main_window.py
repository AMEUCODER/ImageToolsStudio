"""The root window: sidebar | workspace, with a status bar underneath.

MainWindow is the "view" the controller talks to. The controller calls:
    show_image(img)  set_busy(bool, tool)  set_can_undo(bool)  set_status(text)
    show_error(text)  after(ms, fn)  (after() is inherited from tkinter)
"""
from __future__ import annotations

from tkinter import filedialog, messagebox

import customtkinter as ctk

from interface.sidebar import Sidebar
from interface.workspace import Workspace

IMAGE_TYPES = [("Images", "*.png *.jpg *.jpeg *.webp *.bmp *.tif *.tiff"), ("All files", "*.*")]


class MainWindow(ctk.CTk):
    def __init__(self, tool_infos, appearance: str = "dark"):
        ctk.set_appearance_mode(appearance)       # must happen before widgets exist
        ctk.set_default_color_theme("blue")
        super().__init__()

        self.title("Image AI Studio")
        self.geometry("1280x800")
        self.minsize(1000, 650)

        self.controller = None
        self._tools = {info.name: info for info in tool_infos}
        self.current_tool: str | None = None

        # column 1 / row 0 stretch; the sidebar and status bar keep their size
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = Sidebar(self, tool_infos, on_select=self.select_tool)
        self.sidebar.grid(row=0, column=0, sticky="ns")

        self.workspace = Workspace(
            self,
            on_open=self._ask_open,
            on_save=self._ask_save,
            on_undo=lambda: self.controller and self.controller.undo(),
            on_reset=lambda: self.controller and self.controller.reset(),
            on_run=self._run,
        )
        self.workspace.grid(row=0, column=1, sticky="nsew")

        self._status = ctk.CTkLabel(self, text="Ready", anchor="w")
        self._status.grid(row=1, column=0, columnspan=2, sticky="ew", padx=12, pady=(0, 6))

        self.bind("<Control-o>", lambda _e: self._ask_open())
        self.bind("<Control-s>", lambda _e: self._ask_save())
        self.bind("<Control-z>", lambda _e: self.controller and self.controller.undo())

        if tool_infos:
            self.sidebar.select(tool_infos[0].name)
        else:
            self.set_status("No tools found. Check engine/tools/.")

    def bind_controller(self, controller) -> None:
        self.controller = controller

    # ---- user actions ----------------------------------------------------
    def select_tool(self, name: str) -> None:
        self.current_tool = name
        self.workspace.show_tool(self._tools[name])

    def _ask_open(self) -> None:
        path = filedialog.askopenfilename(title="Open image", filetypes=IMAGE_TYPES)
        if path and self.controller:
            self.controller.open_image(path)

    def _ask_save(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Save image", defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg"), ("WebP", "*.webp")],
        )
        if path and self.controller:
            self.controller.save_image(path)

    def _run(self, params: dict) -> None:
        if self.controller and self.current_tool:
            self.controller.run_tool(self.current_tool, params)

    # ---- view interface used by the controller ---------------------------
    def show_image(self, image) -> None:
        self.workspace.show_image(image)

    def set_busy(self, busy: bool, tool: str | None = None) -> None:
        self.workspace.set_run_enabled(not busy)
        if busy:
            label = self._tools[tool].label if tool in self._tools else tool
            self.set_status(f"Processing: {label}...")
        else:
            self.set_status("Done")

    def set_can_undo(self, can_undo: bool) -> None:
        self.workspace.set_can_undo(can_undo)

    def set_status(self, text: str) -> None:
        self._status.configure(text=text)

    def show_error(self, message: str) -> None:
        self.set_status(f"Error: {message}")
        messagebox.showerror("Image AI Studio", message)
