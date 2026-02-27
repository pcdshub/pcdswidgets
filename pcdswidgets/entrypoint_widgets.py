"""
Helper module for creating the [project.entry-points."pydm.widget"]
section in pyproject.toml

python -m pcdswidgets.entrypoint_widgets
"""

import inspect
from pathlib import Path
from typing import cast

import tomlkit as tk
import tomlkit.items as tki

import pcdswidgets.eps_byteindicator
import pcdswidgets.motion
import pcdswidgets.table
import pcdswidgets.vacuum

INCLUDE_MODULES = [
    pcdswidgets.eps_byteindicator,
    pcdswidgets.motion,
    pcdswidgets.table,
    pcdswidgets.vacuum,
]


def main():
    key_val: list[tuple[str, str]] = []
    for module in INCLUDE_MODULES:
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if hasattr(obj, "_qt_designer_"):
                key_val.append((name, f"{obj.__module__}:{name}"))
    key_val.sort()

    pyproj = Path(__file__).parent.parent / "pyproject.toml"
    if not pyproj.exists():
        raise RuntimeError(f"Project file {pyproj} missing?")
    with open(pyproj, "r") as fd:
        toml_doc = tk.parse(fd.read())

    project_table = cast(tki.Table, toml_doc["project"])
    entrypoint_table = cast(tki.Table, project_table["entry-points"])
    widget_table = cast(tki.Table, entrypoint_table["pydm.widget"])
    widget_table.clear()
    for key, value in key_val:
        widget_table[key] = value

    with open(pyproj, "w") as fd:
        tk.dump(toml_doc, fd)


if __name__ == "__main__":
    main()
