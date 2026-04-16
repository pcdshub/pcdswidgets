"""
Generate a fresh version of icon_options.py

This helps us figure out what options exist for designer icons as provided by pydm.
"""

import argparse
import json
from pathlib import Path

from jinja2 import Environment, PackageLoader
from pydm.utilities import iconfont
from qtpy.QtCore import QSize
from qtpy.QtWidgets import QApplication, QGridLayout, QLabel, QMainWindow, QScrollArea, QVBoxLayout, QWidget


def show_icon_options():
    """
    Show a simple qt window with a grid of valid rendered icons alongside their names.

    This is the full set of usable icons from pydm's iconfont.
    """
    app = QApplication([])
    main_window = QMainWindow()
    scroll_area = QScrollArea()
    main_widget = QWidget()
    main_layout = QGridLayout()

    main_window.setCentralWidget(scroll_area)
    scroll_area.setWidgetResizable(True)
    scroll_area.setWidget(main_widget)
    main_widget.setLayout(main_layout)

    cols = 5
    curr = 0
    row = 0

    ifont = iconfont.IconFont()

    for icon_name in get_icon_options():
        icon = ifont.icon(icon_name)
        if icon is None:
            continue

        icon_widget = QWidget()
        icon_layout = QVBoxLayout()
        icon_image = QLabel()
        icon_text = QLabel(icon_name)

        icon_widget.setLayout(icon_layout)
        icon_image.setPixmap(icon.pixmap(QSize(32, 32)))
        icon_layout.addWidget(icon_image)
        icon_layout.addWidget(icon_text)

        main_layout.addWidget(icon_widget, row, curr)
        curr += 1
        if curr >= cols:
            curr = 0
            row += 1

    main_window.resize(1200, 600)
    main_window.show()
    app.exec_()


def generate_icon_options():
    """
    Generate icon_options.py, which contains a large enum with icon options.
    """
    jinja_template = "icon_options.j2"
    env = Environment(trim_blocks=True, loader=PackageLoader("pcdswidgets", "builder"))
    template = env.get_template(jinja_template)
    jinja_output = template.render(
        options=get_icon_options(),
    )
    output_file = Path(__file__).parent / "icon_options.py"
    with open(output_file, "w") as fd:
        fd.write(jinja_output)
        fd.write("\n")


def get_icon_options() -> list[str]:
    """
    Returns the names of all the icons present in pydm's iconfont with valid rendering.
    """
    # The charmap file is everything that pydm recognizes as an icon, including things it has no image data for
    with open(Path(iconfont.__file__).parent / "fontawesome-charmap.json", "r") as fd:
        charmap: dict[str, str] = json.load(fd)

    # The glyph map is everything actually present in the otf file pydm uses
    # I got this map by uploading the otf file to fontdrop.info and copying the glyphIndexMap in the cmap verbatim
    # There are probably other ways to get this info, but this one avoided adding a dependency here
    with open(Path(__file__).parent / "valid_glyph_map.json", "r") as fd:
        glyph_map: dict[str, int] = json.load(fd)
    valid_hex = {hex(int(key))[2:] for key in glyph_map}

    # If something is present in both, it's a valid icon!
    return [name for name, hexval in charmap.items() if hexval in valid_hex]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("show", "build"), default="show")
    args = parser.parse_args()
    if args.mode == "show":
        show_icon_options()
    elif args.mode == "build":
        generate_icon_options()
    else:
        raise RuntimeError(f"Invalid option {args.mode}")
