from pathlib import Path

# relative paths to symbol images stored as a constant

BASE_PATH = Path(__file__).parent / "beamline"


def get_path(filename: str) -> str:
    return str(BASE_PATH / filename)


ATTENUATOR_PATH = get_path("attenuator.png")
IMAGER_PATH = get_path("imager.png")
REFLASER_PATH = get_path("reflaser.png")
SLITS_PATH = get_path("slits.png")
