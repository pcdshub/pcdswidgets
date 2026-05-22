from pathlib import Path

# relative paths to symbol SVGs stored as a constant

BASE_PATH = Path(__file__).parent / "glyphs"

OK = str(BASE_PATH / "ok.svg")

MOVING = str(BASE_PATH / "moving.svg")

WARNING = str(BASE_PATH / "warning.svg")

ERROR = str(BASE_PATH / "error.svg")

DISCONNECTED = str(BASE_PATH / "disconnected.svg")
