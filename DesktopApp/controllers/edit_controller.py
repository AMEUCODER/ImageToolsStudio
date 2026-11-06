import threading


class EditorController:
    def __init__(self, runner, view):
        self.runner = runner
        self.view = view
        self.image = None            # current PIL image

    def load_image(self, path):
        from PIL import Image
        self.image = Image.open(path).convert("RGB")
        self.view.show_result(self.image)

    def run_tool(self, tool_name, params):
        if self.image is None:
            self.view.show_error("Open an image first")
            return
        self.view.set_busy(True)

        def worker():
            try:
                result = self.runner.run(tool_name, self.image, params)
                self.view.after(0, self._done, result)
            except Exception as e:
                self.view.after(0, self._failed, str(e))

        threading.Thread(target=worker, daemon=True).start()

    def _done(self, result):
        self.image = result
        self.view.set_busy(False)
        self.view.show_result(result)

    def _failed(self, msg):
        self.view.set_busy(False)
        self.view.show_error(msg)