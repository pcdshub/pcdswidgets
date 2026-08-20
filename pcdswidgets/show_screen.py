"""
Defines the behavior for the pcdswidgets-show command.

This is a CLI entrypoint that opens screens and widgets as standalone windows.
It exists because it can be difficult to find the full paths to pydm screens included
in this repo once the library is installed in a python environment, rather than just cloned.

Every designer-enabled widget and everything in the "screens" directory are valid targets.
There are named based on their filenames (without the file extension).

For all screens, the arguments map 1:1 to the "macro" names, including casing.
For all widgets, the arguments map 1:1 to the "property" names, including casing.

Most of the help text is generated at runtime, but some screens
and widgets are chosen to be highlighted with hand-written instructions.
"""

import importlib
import inspect
import json
import subprocess
import sys
from argparse import SUPPRESS, ArgumentParser, Namespace
from collections import defaultdict
from itertools import chain
from pathlib import Path
from typing import Protocol

from qtpy.QtGui import QCursor
from qtpy.QtWidgets import QApplication, QWidget

from .builder.build import get_ui_info, process_widget_macros
from .generated.path_defs import SCREEN_PATHS, WIDGET_PATHS

try:
    from qtpy.QtCore import pyqtProperty
except ImportError:
    from qtpy.QtCore import Property as pyqtProperty  # type: ignore

MODULE_PATH = Path(__file__).parent

HIGHLIGHTED_SCREENS = (
    "motor_state_mover_expert",
    "FeatureFinder",
)


def main(args: list[str] | None = None) -> int:
    """Entrypoint for pcdswidgets-show."""
    parser, subparsers = get_parser()

    if args is None:
        args = sys.argv[1:]

    # Pre-parsing for screen, widget names
    # Required because loading all subparsers is too slow
    screen = None
    for arg_text in args:
        if arg_text in chain(SCREEN_PATHS, WIDGET_PATHS):
            screen = arg_text
            if arg_text not in HIGHLIGHTED_SCREENS:
                # We picked a valid screen that needs a generated subparser
                generate_subparser_on_demand(subparsers=subparsers, screen=arg_text)
            # There ought to only be one screen, take the first one
            break

    parsed_args = parser.parse_args(args=args)

    if parsed_args.options:
        show_all_screen_options()
        return 0

    if screen is None:
        print("No screen selected, showing help and exiting", file=sys.stderr)
        parser.print_help()
        return 1

    return open_screen_or_widget(screen=screen, args=parsed_args)


class SubparserAction(Protocol):
    """Helper to type hint the _SubparserAction private type returned by ArgumentParser.add_subparsers()."""

    def add_parser(self, name: str, *, help: str, **kwargs) -> ArgumentParser: ...


def get_parser() -> tuple[ArgumentParser, SubparserAction]:
    """
    The top-level parser without filling in any automatic subparser details.

    This is what will be shown to the user for the main --help text and
    if any of the the highlighted widgets or screens is used.

    If the user picks a non-highlighted widget or screen, the chosen subparser
    will be generated as needed.

    Returns
    -------
    parser, subparsers : ArgumentParser, SubparserAction
        A tuple where the first element is the main parser,
        and the second element is the subparser action
        that we can use to add more subparsers later.
    """
    parser = ArgumentParser(
        prog="pcdswidgets-show",
        description=(
            "Show a pcdswidgets expert screen or single widget as a screen. "
            "Pass --help to individual widget types for specific options."
        ),
    )
    parser.add_argument("--options", action="store_true", help="show all screen and widget options and exit")

    # Add only the highlighted subparsers! The others will be added later, when needed.
    subparsers = parser.add_subparsers(title="highlighted screens", required=False)

    # State mover expert screen is distributed in pcdswidgets and is useful standalone
    # The macros are not naively discoverable, but they are documented and implemented here.
    motor_state_mover_expert = subparsers.add_parser("motor_state_mover_expert", help="Expert screen for state movers")
    motor_state_mover_expert.add_argument("--DEVICE", action="store", required=True, help="Base prefix, e.g. TST:D3")
    motor_state_mover_expert.add_argument(
        "--PMPS", action="store_true", required=False, help="Select PMPS-enabled variant"
    )
    motor_state_mover_expert.add_argument("--STATE_COUNT", action="store", type=int, help="Number states, e.g. 4")
    motor_state_mover_expert.add_argument(
        "--DEVICE_TOKENS", action="store", help="comma-separated per-device tokens, e.g. D1M1,D2M1,D3M1"
    )

    # FeatureFinder can function as if it was a standalone app, so it's mostly used standalone.
    feature_finder = subparsers.add_parser("FeatureFinder", help="Live plotting GUI")
    feature_finder.add_argument("--detector", action="store", required=True, help="PV value to plot on the y-axis.")
    feature_finder.add_argument(
        "--motor", action="store", required=True, help="Base PV for motor to move and to plot on the x-axis."
    )

    return parser, subparsers


def generate_subparser_on_demand(subparsers: SubparserAction, screen: str):
    """Add a subparser with generated help text for a screen or widget."""
    if screen in SCREEN_PATHS:
        return generate_subparser_from_screen(subparsers=subparsers, screen=screen)
    if screen in WIDGET_PATHS:
        return generate_subparser_from_widget(subparsers=subparsers, widget=screen)
    raise ValueError(f"{screen} is not a valid screen or widget type.")


def generate_subparser_from_screen(subparsers: SubparserAction, screen: str):
    """
    Add a subparser with generated help text for a screen.

    Each macro discoverable in the screen file is exposed as a same-named cli argument.
    """
    parser = subparsers.add_parser(name=screen, help=f"Opens the {screen} screen")
    ui_info = get_ui_info(str(MODULE_PATH / SCREEN_PATHS[screen]))
    jinja_info = process_widget_macros(ui_info=ui_info)
    for macro in sorted(jinja_info.macro_set):
        parser.add_argument(f"--{macro}")


def generate_subparser_from_widget(subparsers: SubparserAction, widget: str):
    """
    Add a subparser with generated help text for a widget.

    Each property created using pyqt is exposed as a same-named cli argument.
    """
    module_name, widget_import_name = WIDGET_PATHS[widget].split(":")
    WidgetType = getattr(importlib.import_module(module_name), widget_import_name)
    widget_doc = inspect.getdoc(WidgetType)
    if isinstance(widget_doc, str):
        widget_doc = widget_doc.split("\n")[0]
    else:
        widget_doc = ""
    parser = subparsers.add_parser(name=widget, help=widget_doc)
    for name, val in inspect.getmembers(WidgetType):
        if name == "rules":
            # pydm rules don't make sense here, skip to avoid confusion
            continue
        if isinstance(val, pyqtProperty):
            prop_doc = inspect.getdoc(val.fget)
            if isinstance(prop_doc, str):
                prop_doc = prop_doc.split("\n")[0]
            parser.add_argument(f"--{name}", default=SUPPRESS, help=prop_doc)


def get_widget_type(widget: str) -> type[QWidget]:
    """Return the actual class (type) associated with a widget name."""
    module_name, widget_import_name = WIDGET_PATHS[widget].split(":")
    return getattr(importlib.import_module(module_name), widget_import_name)


def show_all_screen_options():
    """
    Show the user all of the possible screens that they could open using pcdswidgets-show.

    At first, only the highlighted screens and widgets are shown in the help text.
    This keeps the help text focused to the most useful screens without overwhelming the user.

    If the user invokes the --options argument, this function will be called to
    show every single possibility, split into category by filepath and import path.
    """
    screen_categories: dict[str, list[str]] = defaultdict(list)
    for screen_name, screen_path in SCREEN_PATHS.items():
        category = str(Path(screen_path).parent)
        screen_categories[category].append(screen_name)
    widget_categories: dict[str, list[str]] = defaultdict(list)
    for widget_name, widget_import in WIDGET_PATHS.items():
        module_name = widget_import.split(":")[0]
        category = ".".join(module_name.split(".")[1:3])
        widget_categories[category].append(widget_name)

    print("# Available Screens:")
    for category in sorted(screen_categories):
        print()
        print(f"## {category}")
        print()
        for screen_name in sorted(screen_categories[category]):
            print(screen_name)

    print()
    print("# Available Widgets:")
    for category in sorted(widget_categories):
        print()
        print(f"## {category}")
        print()
        for widget_name in sorted(widget_categories[category]):
            print(widget_name)


def open_screen_or_widget(screen: str, args: Namespace) -> int:
    """Open a named screen or widget with the given parsed aruguments."""
    if screen in SCREEN_PATHS:
        return open_screen(screen=screen, args=args)
    if screen in WIDGET_PATHS:
        open_widget(widget=screen, args=args)
        return 0

    print(f"Screen {screen} not found in pcdswidgets, exiting.")
    return 1


def open_screen(screen: str, args: Namespace) -> int:
    """Open a screen stored in pcdswidgets using pydm."""
    macros = json.dumps(vars(args))
    full_screen_path = str(MODULE_PATH / SCREEN_PATHS[screen])
    proc = subprocess.run(
        ["pydm", "--hide-nav-bar", "--hide-menu-bar", "--hide-status-bar", "-m", macros, full_screen_path]
    )
    return proc.returncode


def open_widget(widget: str, args: Namespace):
    """Open a widget defined in pcdswidgets as a screen by creating a mini QApplication."""
    app = QApplication([])
    widget_obj = get_widget_type(widget=widget)()
    for prop, value in vars(args).items():
        if prop != "widget":
            # Note: assuming that everything is settable as a string- may not be true!
            widget_obj.setProperty(prop, value)
    widget_obj.move(QCursor.pos())
    widget_obj.show()
    app.exec_()


if __name__ == "__main__":
    sys.exit(main())
