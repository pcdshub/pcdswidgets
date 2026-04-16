"""
Helper module for creating the [project.entry-points."pydm.widget"]
section in pyproject.toml

python -m pcdswidgets.builder.entrypoint_finder
"""

import importlib
import inspect
import pkgutil
from pathlib import Path
from types import ModuleType
from typing import Iterator, cast

import tomlkit as tk
import tomlkit.items as tki
from qtpy.QtWidgets import QWidget

import pcdswidgets

SKIP_WIDGETS = []

SKIP_MODULES = [
    ".tests",
    ".demo",
    ".ui",
]


def main():
    key_val = get_widget_entrypoint_data()
    widget_table, toml_doc = get_current_widget_table()
    update_widget_table(widget_table, key_val)
    write_pyproj(toml_doc)


def get_widget_entrypoint_data() -> list[tuple[str, str]]:
    key_val_set: set[tuple[str, str]] = set()
    for name, WidgetCls in iter_all_widgets():
        key_val_set.add((name, f"{WidgetCls.__module__}:{name}"))
    key_val = sorted(key_val_set)
    return key_val


def iter_all_widgets() -> Iterator[tuple[str, type[QWidget]]]:
    """
    Recursively yield all widgets to export from pcdswidgets.

    Yields
    ------
    name, widget: str, QWidget
    """
    seen: set[str] = set()
    for module in iter_submodules():
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if name in SKIP_WIDGETS:
                continue
            if name in seen:
                continue
            if issubclass(obj, QWidget) and hasattr(obj, "_qt_designer_"):
                seen.add(name)
                yield (name, obj)


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


def get_pyproj_path() -> Path:
    return Path(pcdswidgets.__file__).parent.parent / "pyproject.toml"


def get_current_widget_table() -> tuple[tki.Table, tk.TOMLDocument]:
    pyproj = get_pyproj_path()
    if not pyproj.exists():
        raise RuntimeError(f"Project file {pyproj} missing?")
    with open(pyproj, "r") as fd:
        toml_doc = tk.parse(fd.read())

    project_table = cast(tki.Table, toml_doc["project"])
    entrypoint_table = cast(tki.Table, project_table["entry-points"])
    widget_table = cast(tki.Table, entrypoint_table["pydm.widget"])

    return widget_table, toml_doc


def update_widget_table(widget_table: tki.Table, key_val: list[tuple[str, str]]):
    widget_table.clear()
    for key, value in key_val:
        widget_table[key] = value


def write_pyproj(toml_doc: tk.TOMLDocument):
    pyproj = get_pyproj_path()
    with open(pyproj, "w") as fd:
        tk.dump(toml_doc, fd)


if __name__ == "__main__":
    main()
