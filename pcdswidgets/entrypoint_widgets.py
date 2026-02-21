"""
Helper module for creating the [project.entry-points."pydm.widget"]
section in pyproject.toml

python -m pcdswidgets.entrypoint_widgets
"""

import inspect

import pcdswidgets.eps_byteindicator
import pcdswidgets.table
import pcdswidgets.vacuum

INCLUDE_MODULES = [pcdswidgets.eps_byteindicator, pcdswidgets.table, pcdswidgets.vacuum]


def main():
    lines = set()
    for module in INCLUDE_MODULES:
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if hasattr(obj, "_qt_designer_"):
                lines.add(f'{name} = "{obj.__module__}:{name}"')
    for line in sorted(lines):
        print(line)


if __name__ == "__main__":
    main()
