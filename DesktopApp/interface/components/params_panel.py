"""Builds the option controls at the bottom of the window from a tool's ParamSpec list.

Because the controls come from the specs, adding a tool or a parameter on the engine
side needs NO change here. Supported kinds: slider, int, choice, bool, text, color.
With more than 3 options the panel switches to two columns.
"""
from __future__ import annotations

from tkinter import colorchooser

import customtkinter as ctk


def _text_on(hex_color: str) -> str:
    """Black or white text, whichever is readable on this background color."""
    try:
        r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    except ValueError:
        return "black"
    return "black" if (r * 299 + g * 587 + b * 114) / 1000 > 140 else "white"


class ParamsPanel(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self._specs = []
        self._vars = {}
        self._setters = {}

    # ---- building --------------------------------------------------------
    def show(self, info) -> None:
        for child in self.winfo_children():
            child.destroy()
        self._vars.clear()
        self._setters.clear()
        self._specs = list(info.params)

        if not self._specs:
            ctk.CTkLabel(self, text="This tool has no options.", text_color="gray").grid(
                row=0, column=0, sticky="w", padx=8, pady=6
            )
            return

        columns = 2 if len(self._specs) > 3 else 1
        for col in range(2):
            self.grid_columnconfigure(col, weight=1 if col < columns else 0)

        for index, spec in enumerate(self._specs):
            cell = ctk.CTkFrame(self, fg_color="transparent")
            cell.grid(row=index // columns, column=index % columns, sticky="ew", padx=6, pady=3)
            cell.grid_columnconfigure(1, weight=1)
            ctk.CTkLabel(cell, text=spec.label, anchor="w", width=110).grid(row=0, column=0, sticky="w", padx=(2, 10))
            self._build_control(cell, spec)
            if spec.help:
                ctk.CTkLabel(cell, text=spec.help, anchor="w", text_color="gray",
                             font=ctk.CTkFont(size=11)).grid(row=1, column=1, columnspan=2, sticky="w")

    def _build_control(self, cell, spec) -> None:
        kind = spec.kind
        if kind in ("slider", "int"):
            var = ctk.DoubleVar(value=spec.default)
            value_label = ctk.CTkLabel(cell, width=46, anchor="e", text=self._fmt(spec, spec.default))
            steps = None
            if kind == "int":
                steps = int(spec.max - spec.min)
            elif spec.step:
                steps = int(round((spec.max - spec.min) / spec.step))
            ctk.CTkSlider(
                cell, from_=spec.min, to=spec.max, variable=var, number_of_steps=steps,
                command=lambda v, s=spec, lbl=value_label: lbl.configure(text=self._fmt(s, v)),
            ).grid(row=0, column=1, sticky="ew")
            value_label.grid(row=0, column=2, padx=(6, 2))
            self._setters[spec.name] = lambda v, s=spec, var=var, lbl=value_label: (
                var.set(v), lbl.configure(text=self._fmt(s, v)))

        elif kind == "choice":
            var = ctk.StringVar(value=spec.default)
            ctk.CTkOptionMenu(cell, values=list(spec.choices), variable=var).grid(row=0, column=1, sticky="w")
            self._setters[spec.name] = var.set

        elif kind == "bool":
            var = ctk.BooleanVar(value=bool(spec.default))
            ctk.CTkSwitch(cell, text="", variable=var).grid(row=0, column=1, sticky="w")
            self._setters[spec.name] = var.set

        elif kind == "text":
            var = ctk.StringVar(value=str(spec.default))
            ctk.CTkEntry(cell, textvariable=var).grid(row=0, column=1, sticky="ew")
            self._setters[spec.name] = var.set

        elif kind == "color":
            var = ctk.StringVar(value=spec.default)
            button = ctk.CTkButton(cell, width=110, text=spec.default)

            def paint(value, b=button):
                b.configure(text=value, fg_color=value, hover_color=value, text_color=_text_on(value))

            def pick(v=var, label=spec.label):
                _rgb, hex_value = colorchooser.askcolor(color=v.get(), title=label)
                if hex_value:
                    v.set(hex_value)
                    paint(hex_value)

            button.configure(command=pick)
            paint(spec.default)
            button.grid(row=0, column=1, sticky="w")
            self._setters[spec.name] = lambda value, v=var: (v.set(value), paint(value))

        else:
            ctk.CTkLabel(cell, text=f"(unsupported option type: {kind})", text_color="gray").grid(
                row=0, column=1, sticky="w")
            return
        self._vars[spec.name] = var

    @staticmethod
    def _fmt(spec, value) -> str:
        if spec.kind == "int":
            return str(int(round(float(value))))
        return f"{float(value):.2f}".rstrip("0").rstrip(".")

    # ---- reading / resetting ---------------------------------------------
    def values(self) -> dict:
        """Current control values. The engine validates and clamps them again."""
        out = {}
        for spec in self._specs:
            raw = self._vars[spec.name].get()
            out[spec.name] = int(round(raw)) if spec.kind == "int" else raw
        return out

    def reset(self) -> None:
        """Put every control back to its default."""
        for spec in self._specs:
            setter = self._setters.get(spec.name)
            if setter:
                setter(spec.default)
