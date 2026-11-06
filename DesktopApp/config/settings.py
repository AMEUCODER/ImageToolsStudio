"""User settings: data/settings.json, overridable with environment variables.

    IMAGE_STUDIO_MODE=remote  IMAGE_STUDIO_SERVER=http://127.0.0.1:8000  python run_desktop.py
"""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass

from config.paths import SETTINGS_FILE


@dataclass
class Settings:
    mode: str = "local"                       # "local" or "remote"
    server_url: str = "http://127.0.0.1:8000"
    token: str = ""
    appearance: str = "dark"                  # "dark", "light" or "system"


def load_settings() -> Settings:
    settings = Settings()
    if SETTINGS_FILE.exists():
        try:
            data = json.loads(SETTINGS_FILE.read_text("utf-8"))
            for key, value in data.items():
                if hasattr(settings, key):
                    setattr(settings, key, value)
        except (OSError, json.JSONDecodeError):
            pass                              # a broken file falls back to defaults

    settings.mode = os.environ.get("IMAGE_STUDIO_MODE", settings.mode)
    settings.server_url = os.environ.get("IMAGE_STUDIO_SERVER", settings.server_url)
    settings.token = os.environ.get("IMAGE_STUDIO_TOKEN", settings.token)
    return settings


def save_settings(settings: Settings) -> None:
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(asdict(settings), indent=2), "utf-8")
