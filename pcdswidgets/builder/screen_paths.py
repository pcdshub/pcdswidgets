"""
Updates the generated/path_defs.py file used by pcdswidgets-show.

The file contains information about the screen and widget options that would otherwise
need to be inspected more slowly at runtime. It is generated as a python file instead of e.g. json
so it can be imported from bytecode at runtime instead of parsed from text data.

The widgets are sourced directly from pyproject.toml.
The screens are sourced by scraping the "screens" folder.
"""

from pathlib import Path

from jinja2 import Environment, PackageLoader

from .entrypoint_finder import get_current_widget_table

MODULE_ROOT = Path(__file__).parent.parent


def main():
    """Entrypoint for pcdswidgets.builder.screen_paths."""
    print("Loading screen paths")
    screen_paths = get_screen_paths()

    print("Loading widget imports")
    table = get_current_widget_table()[0]
    # This is a mapping from widget name to fully qualified import name
    # e.g. WidgetName: pcdswidgets.common.something.long_name:WidgetName
    widget_imports = dict(table)

    print("Writing out generated/path_deps.py file")
    write_path_defs(screen_paths=screen_paths, widget_imports=widget_imports)


def get_screen_paths() -> dict[str, str]:
    """Return a dict mapping from screen name to relative path."""
    screen_tups: list[tuple[str, str]] = []
    for ext in ("py", "ui"):
        for filepath in (MODULE_ROOT / "screens").rglob(f"*.{ext}"):
            screen_tups.append((filepath.stem, str(filepath.relative_to(MODULE_ROOT))))
    screen_paths: dict[str, str] = {}
    for name, pathstr in sorted(screen_tups):
        screen_paths[name] = pathstr
    return screen_paths


def write_path_defs(screen_paths: dict[str, str], widget_imports: dict[str, str]):
    """Write out the generated/path_defs.py file given the input mappings."""
    jinja_template = "path_defs.py.j2"
    env = Environment(trim_blocks=True, loader=PackageLoader("pcdswidgets", "builder"))
    template = env.get_template(jinja_template)
    jinja_output = template.render(
        jinja_template=jinja_template,
        screen_paths=screen_paths,
        widget_imports=widget_imports,
    )
    output_file = MODULE_ROOT / "generated" / "path_defs.py"
    with open(output_file, "w") as fd:
        fd.write(jinja_output + "\n")


if __name__ == "__main__":
    main()
