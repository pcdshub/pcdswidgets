"""
Helper module for creating the [project.entry-points."pydm.widget"]
section in pyproject.toml

python -m pcdswidgets.entrypoint_widgets
"""

import importlib
import inspect
import pkgutil
from pathlib import Path
from types import ModuleType
from typing import Iterator, cast

import tomlkit as tk
import tomlkit.items as tki

SKIP_WIDGETS = [
    "PCDSSymbolBase",
]

SKIP_MODULES = [
    ".tests",
    ".demo",
]


def main():
    key_val: list[tuple[str, str]] = []
    for module in iter_submodules():
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if name in SKIP_WIDGETS:
                continue
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


def iter_submodules(package: str = "pcdswidgets") -> Iterator[ModuleType]:
    """Recursively yield all submodules of a package."""
    if any(mod in package for mod in SKIP_MODULES):
        return
    module = importlib.import_module(package)
    yield module
    try:
        for _, modname, _ in pkgutil.walk_packages(module.__path__, module.__name__ + "."):
            if "__main__" not in modname:
                yield from iter_submodules(modname)
    except AttributeError:
        ...


if __name__ == "__main__":
    main()
