import customtkinter as ctk
from interface.sidebar import Sidebar
from interface.workspace import Workspace


class App(ctk.CTk):
    def __init__(self, tool_names):
        ctk.set_appearance_mode("dark")          # before creating the window
        ctk.set_default_color_theme("blue")
        super().__init__()

        self.title("Image AI Studio")
        self.geometry("1280x800")
        self.minsize(1000, 650)

        # column 1 and row 0 stretch; everything else keeps its size
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = Sidebar(self, tool_names, on_select=self._on_tool_selected)
        self.sidebar.grid(row=0, column=0, sticky="ns")

        self.workspace = Workspace(self, on_run=self._on_run)
        self.workspace.grid(row=0, column=1, sticky="nsew")

        self.status = ctk.CTkLabel(self, text="Ready", anchor="w")
        self.status.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=4)

        self.controller = None
        self.current_tool = tool_names[0] if tool_names else None

    def bind_controller(self, controller):
        self.controller = controller

    def _on_tool_selected(self, tool_name):
        self.current_tool = tool_name
        self.workspace.show_params_for(tool_name)

    def _on_run(self, params):
        self.controller.run_tool(self.current_tool, params)

    # methods the controller calls (the "view" interface)
    def set_busy(self, busy):
        self.status.configure(text="Processing..." if busy else "Ready")
        self.workspace.set_run_enabled(not busy)

    def show_result(self, pil_image):
        self.workspace.canvas.show(pil_image)

    def show_error(self, message):
        self.status.configure(text=f"Error: {message}")

app = App(tool_names=runner.list_tools())
controller = EditorController(runner=runner, view=app)
app.bind_controller(controller)
app.mainloop()