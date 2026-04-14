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

    main_window.resize(800, 600)
    main_window.show()
    app.exec_()


def generate_icon_options():
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
    with open(Path(iconfont.__file__).parent / "fontawesome-charmap.json", "r") as fd:
        charmap: dict[str, str] = json.load(fd)
    return list(charmap)


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
