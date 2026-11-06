# DesktopApp/run_desktop.py
from config.settings import load_settings
from controllers.editor_controller import EditorController
from engine.engine import Engine
from interface.main_window import MainWindow
from runners.local_runner import LocalRunner
from runners.remote_runner import RemoteRunner


def main():
    settings = load_settings()

    if settings.mode == "remote":
        runner = RemoteRunner(settings.server_url, settings.token)
    else:
        runner = LocalRunner(Engine())

    window = MainWindow(tool_infos=runner.describe_tools(), appearance=settings.appearance)
    controller = EditorController(runner=runner, view=window)
    window.bind_controller(controller)
    window.mainloop()          # blocks here until the window is closed
    runner.close()


if __name__ == "__main__":
    main()
