"""
CLI entrypoint for opening expert screens and other widgets as standalone windows.

Every designer-enabled widget and everything in the "screens" directory are valid targets.

These are included in an automated way, but some screens and widgets are chosen
to be highlighted in the --help text with hand-written instructions.
"""

import importlib
import inspect
import json
import subprocess
from argparse import SUPPRESS, ArgumentError, ArgumentParser, ArgumentTypeError, Namespace
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
    # "FeatureFinder",
    # "MotorBeckhoffSlits",
)


def main(args: list[str] | None = None) -> int:
    pre_parser = get_pre_parser()
    base_parser, subparsers = get_base_parser()
    try:
        pre_args = pre_parser.parse_args(args=args)
    except (ArgumentError, ArgumentTypeError) as exc:
        base_parser.parse_args(args=args)
        # Backup error in case something has gone very wrong
        raise RuntimeError("Issue in argument setup") from exc
    if pre_args.show_all_screens:
        show_all_screens()
        return 0
    screen = None
    if pre_args.pos_inputs:
        screen = pre_args.pos_inputs[0]
        if screen not in HIGHLIGHTED_SCREENS:
            if screen in chain(SCREEN_PATHS, WIDGET_PATHS):
                generate_subparser_on_demand(subparsers=subparsers, screen=pre_args.pos_inputs[0])
            else:
                base_parser.parse_args(args=args)
                # Backup error in case something has gone very wrong
                raise RuntimeError("Invalid screen type {screen}")
    base_args = base_parser.parse_args(args=args)

    if screen is None:
        # Unclear if we can get here
        print("No screen selected, exiting")
        return 1
    return open_screen_or_widget(screen=screen, args=base_args)


class SubparserAction(Protocol):
    def add_parser(self, name: str, *, help: str, **kwargs) -> ArgumentParser: ...


def get_base_parser() -> tuple[ArgumentParser, SubparserAction]:
    """
    The top-level parser without filling in any automatic subparser details.

    This is what will be shown to the user for the main --help text and
    if any of the the highlighted widgets or screens is used.

    If the user picks a non-highlighted widget or screen, the chosen subparser
    will be generated as needed.
    """
    parser = ArgumentParser(
        prog="pcdswidgets-show",
        description=(
            "Show a pcdswidgets expert screen or single widget as a screen. "
            "Pass --help to individual widget types for specific options."
        ),
    )
    parser.add_argument("--show-all-screens", action="store_true", help="show all screen and widget options and exit")

    subparsers = parser.add_subparsers(title="highlighted screens", required=True)

    # Add only the highlighted subparsers! The others will be added later, when needed.
    motor_state_mover_expert = subparsers.add_parser("motor_state_mover_expert", help="Expert screen for state movers")
    motor_state_mover_expert.add_argument("--DEVICE", action="store", required=True, help="Base prefix, e.g. TST:D3")
    motor_state_mover_expert.add_argument(
        "--PMPS", action="store_true", required=False, help="Select PMPS-enabled variant"
    )
    motor_state_mover_expert.add_argument("--STATE_COUNT", action="store", type=int, help="Number states, e.g. 4")
    motor_state_mover_expert.add_argument(
        "--DEVICE_TOKENS", action="store", help="comma-separated per-device tokens, e.g. D1M1,D2M1,D3M1"
    )
    # TODO fill these in? trying to figure out other parts of this first
    # feature_finder = subparsers.add_parser("FeatureFinder", help="Live plotting GUI")
    # motor_beckhoff_slits = subparsers.add_parser("MotorBeckhoffSlits", help="Expert screen for beckhoff slits.")

    return parser, subparsers


def get_pre_parser() -> ArgumentParser:
    """Parser to determine if any subparsers need to be generated."""
    parser = ArgumentParser(prog="pcdswidgets-show", add_help=False)
    parser.add_argument("--show-all-screens", action="store_true")
    parser.add_argument("--help", action="store_true")
    parser.add_argument("pos_inputs", nargs="*")
    return parser


def generate_subparser_on_demand(subparsers: SubparserAction, screen: str):
    if screen in SCREEN_PATHS:
        return generate_subparser_from_screen(subparsers=subparsers, screen=screen)
    if screen in WIDGET_PATHS:
        return generate_subparser_from_widget(subparsers=subparsers, widget=screen)
    raise ValueError(f"{screen} is not a valid screen or widget type.")


def generate_subparser_from_screen(subparsers: SubparserAction, screen: str):
    parser = subparsers.add_parser(name=screen, help=f"Opens the {screen} screen")
    # parser.set_defaults(pcdswidgets_screen_variable=screen)
    ui_info = get_ui_info(str(MODULE_PATH / SCREEN_PATHS[screen]))
    jinja_info = process_widget_macros(ui_info=ui_info)
    for macro in sorted(jinja_info.macro_set):
        parser.add_argument(f"--{macro}")


def generate_subparser_from_widget(subparsers: SubparserAction, widget: str):
    module_name, widget_import_name = WIDGET_PATHS[widget].split(":")
    WidgetType = getattr(importlib.import_module(module_name), widget_import_name)
    widget_doc = inspect.getdoc(WidgetType)
    if isinstance(widget_doc, str):
        widget_doc = widget_doc.split("\n")[0]
    else:
        widget_doc = ""
    parser = subparsers.add_parser(name=widget, help=widget_doc)
    # parser.set_defaults(pcdswidgets_screen_variable=widget)
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
    module_name, widget_import_name = WIDGET_PATHS[widget].split(":")
    return getattr(importlib.import_module(module_name), widget_import_name)


def show_all_screens():
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
    if screen in SCREEN_PATHS:
        return open_screen(screen=screen, args=args)
    if screen in WIDGET_PATHS:
        open_widget(widget=screen, args=args)
        return 0

    print(f"Screen {screen} not found in pcdswidgets, exiting.")
    return 1


def open_screen(screen: str, args: Namespace) -> int:
    macros = json.dumps(vars(args))
    full_screen_path = str(MODULE_PATH / SCREEN_PATHS[screen])
    proc = subprocess.run(
        ["pydm", "--hide-nav-bar", "--hide-menu-bar", "--hide-status-bar", "-m", macros, full_screen_path]
    )
    return proc.returncode


def open_widget(widget: str, args: Namespace):
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
    main()
