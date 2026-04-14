"""
Generate a fresh version of icon_options.py

This helps us figure out what options exist for designer icons as provided by pydm.
"""

import json
from pathlib import Path

from jinja2 import Environment, PackageLoader
from pydm.utilities import iconfont


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
    generate_icon_options()
