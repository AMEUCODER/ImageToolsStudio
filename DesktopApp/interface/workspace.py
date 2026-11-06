"""The right-hand area: toolbar on top, image canvas in the middle, options + Run below.

Workspace only draws widgets and reports clicks through the callbacks it is given.
It knows nothing about the engine, runners or the controller.
"""
from __future__ import annotations

import customtkinter as ctk

from interface.canvas import Canvas
from interface.components.params_panel import ParamsPanel


class Workspace(ctk.CTkFrame):
    def __init__(self, master, on_open, on_save, on_undo, on_reset, on_run):
        super().__init__(master, corner_radius=0, fg_color="transparent")
        self._on_run = on_run
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)          # the canvas takes all spare space

        # --- toolbar (row 0) ---
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 6))
        ctk.CTkButton(toolbar, text="Open", width=80, command=on_open).pack(side="left", padx=(0, 6))
        ctk.CTkButton(toolbar, text="Save", width=80, command=on_save).pack(side="left", padx=6)
        self._undo_button = ctk.CTkButton(toolbar, text="Undo", width=80, command=on_undo, state="disabled")
        self._undo_button.pack(side="left", padx=6)
        ctk.CTkButton(toolbar, text="Original", width=80, command=on_reset, fg_color="gray40",
                      hover_color="gray30").pack(side="left", padx=6)
        self._tool_title = ctk.CTkLabel(toolbar, text="", font=ctk.CTkFont(size=16, weight="bold"))
        self._tool_title.pack(side="right", padx=8)

        # --- canvas (row 1) ---
        self.canvas = Canvas(self)
        self.canvas.grid(row=1, column=0, sticky="nsew", padx=10, pady=4)

        # --- options + run (row 2) ---
        bottom = ctk.CTkFrame(self)
        bottom.grid(row=2, column=0, sticky="ew", padx=10, pady=(6, 10))
        bottom.grid_columnconfigure(0, weight=1)
        self._description = ctk.CTkLabel(bottom, text="", anchor="w", text_color="gray", wraplength=700, justify="left")
        self._description.grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 0))
        self._params = ParamsPanel(bottom)
        self._params.grid(row=1, column=0, sticky="ew", padx=4, pady=4)
        buttons = ctk.CTkFrame(bottom, fg_color="transparent")
        buttons.grid(row=0, column=1, rowspan=2, padx=14, pady=10)
        self._run_button = ctk.CTkButton(buttons, text="Run", width=120, height=42, command=self._run_clicked)
        self._run_button.pack()
        ctk.CTkButton(buttons, text="Reset options", width=120, height=26, fg_color="transparent",
                      border_width=1, text_color=("gray20", "gray80"),
                      command=lambda: self._params.reset()).pack(pady=(8, 0))

    # --- called by MainWindow ---
    def show_tool(self, info) -> None:
        self._tool_title.configure(text=info.label)
        self._description.configure(text=info.description)
        self._params.show(info)

    def show_image(self, image) -> None:
        self.canvas.show(image)

    def set_run_enabled(self, enabled: bool) -> None:
        self._run_button.configure(state="normal" if enabled else "disabled",
                                   text="Run" if enabled else "Working...")

    def set_can_undo(self, can_undo: bool) -> None:
        self._undo_button.configure(state="normal" if can_undo else "disabled")

    def _run_clicked(self) -> None:
        self._on_run(self._params.values())
