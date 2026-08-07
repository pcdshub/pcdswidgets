"""
CLI entrypoint for opening expert screens and other widgets as standalone windows.
"""

import argparse
import inspect
from collections import defaultdict

from qtpy.QtGui import QCursor
from qtpy.QtWidgets import QApplication, QWidget

from .builder.entrypoint_finder import iter_all_widgets

try:
    from qtpy.QtCore import pyqtProperty
except ImportError:
    from qtpy.QtCore import Property as pyqtProperty  # type: ignore


def main():
    widget_types: dict[str, type[QWidget]] = {}
    widget_names_by_category: dict[str, list[str]] = defaultdict(list)
    for name, WidgetType in iter_all_widgets():
        module = inspect.getmodule(WidgetType)
        if module is None:
            continue
        category = ".".join(module.__name__.split(".")[1:][:2])
        widget_types[name] = WidgetType
        widget_names_by_category[category].append(name)

    widget_type_help = ""

    for category in sorted(widget_names_by_category):
        widget_type_help += f"{category}:\n"
        widget_type_help += " ".join(sorted(widget_names_by_category[category])) + "\n\n"

    parser = argparse.ArgumentParser(
        prog="pcdswidgets-show",
        description="Show a single widget as a screen. See help text for individual widget types for options.",
        epilog=widget_type_help,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(title="widget types", required=True, metavar="WidgetType")

    for name, WidgetType in widget_types.items():
        sp = subparsers.add_parser(name=name)
        sp.set_defaults(widget=name)
        for name, val in inspect.getmembers(WidgetType):
            if name == "rules":
                # pydm rules don't make sense here, skip to avoid confusion
                continue
            if isinstance(val, pyqtProperty):
                doc = inspect.getdoc(val.fget)
                if isinstance(doc, str):
                    doc = doc.split("\n")[0]
                sp.add_argument(f"--{name}", default=argparse.SUPPRESS, help=doc)

    app = QApplication([])
    args = parser.parse_args()
    widget = widget_types[args.widget]()
    for prop, value in vars(args).items():
        if prop != "widget":
            # Note: assuming that everything is settable as a string- may not be true!
            widget.setProperty(prop, value)
    widget.move(QCursor.pos())
    widget.show()
    app.exec_()


if __name__ == "__main__":
    main()
