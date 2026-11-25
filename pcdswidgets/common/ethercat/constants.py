"""
Constants shared by the EtherCAT terminal-state widgets and the discovery CLI.

Kept free of Qt / PyDM imports so :mod:`pcdswidgets.common.ethercat.discover`
(run as a subprocess) stays lightweight.
"""

from __future__ import annotations

import os
from pathlib import Path

# Default location of the discovery files: ``~/.cache/ecat-states/<plc>.json``.
CACHE_DIR = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "ecat-states"

# Enum strings in record order (pytmc/ethercat.py). Live mode uses the strings
# reported by Channel Access; these are the fallback and the mock definition.
STATE_ENUM = ("INIT", "PREOP", "BOOTSTRAP", "SAFEOP", "OP")
LINK_ENUM = (
    "OK",
    "NOT_PRESENT",
    "LINK_WITHOUT_COMM",
    "MISSING_LINK",
    "ADDITIONAL_LINK",
    "PORT_A",
    "PORT_B",
    "PORT_C",
    "PORT_D",
    "MULTIPLE_FLAGS",
)

TRUTHY = frozenset({"1", "true", "yes", "on"})


def to_bool(value) -> bool:
    """Property / macro value as a bool: strings are truthy if in :data:`TRUTHY`."""
    if isinstance(value, str):
        return value.strip().lower() in TRUTHY
    return bool(value)
