"""Left column: one button per tool, built from the tool list."""
from __future__ import annotations

import customtkinter as ctk

SELECTED = ("gray75", "gray28")


class Sidebar(ctk.CTkScrollableFrame):
    def __init__(self, master, tool_infos, on_select):
        super().__init__(master, width=190, corner_radius=0, label_text="Tools")
        self._on_select = on_select
        self._buttons = {}
        for info in tool_infos:
            button = ctk.CTkButton(
                self, text=info.label, anchor="w", fg_color="transparent",
                text_color=("gray10", "gray90"), hover_color=("gray80", "gray25"),
                command=lambda name=info.name: self.select(name),   # name=... binds per button
            )
            button.pack(fill="x", pady=2)
            self._buttons[info.name] = button

    def select(self, name: str) -> None:
        for tool_name, button in self._buttons.items():
            button.configure(fg_color=SELECTED if tool_name == name else "transparent")
        self._on_select(name)
