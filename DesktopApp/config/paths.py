"""Where the desktop app keeps its own files."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent          # .../DesktopApp
DATA_DIR = ROOT / "data"
OUTPUT_DIR = DATA_DIR / "outputs"
CACHE_DIR = DATA_DIR / "cache"
SETTINGS_FILE = DATA_DIR / "settings.json"
