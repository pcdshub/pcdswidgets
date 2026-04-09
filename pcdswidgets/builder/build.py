import argparse
import dataclasses
import os
import re
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

from jinja2 import Environment, PackageLoader
from qtpy.uic import compileUi  # type: ignore


def build_uic(designer_ui: str, output_dir: str = ""):
    """
    Use the standard uic parser to create a .py file with a .ui file's widget layouts.

    The files are named systematically with patterns like:
    some_name.ui -> some_name_form.py
    """
    output_dir_path = get_output_path(designer_ui=designer_ui, default_base="generated", output_dir=output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)
    output_file = output_dir_path / os.path.basename(designer_ui).replace(".ui", "_form.py")
    with open(output_file, "w") as fd:
        compileUi(designer_ui, fd)
    build_inits(base_dir=output_dir_path)


def build_base_widget(designer_ui: str, output_dir: str = ""):
    """
    Create a .py file with a suitable base widget for inclusion in designer.

    The files are named systematically with patterns like:
    some_name.ui -> some_name_base.py

    The base widget will have the following properties:
    - Imports from the uic output for its widget layouts
    - Has appropriately-named properties for any expected macros in the pydm source file
    - Has type hints to help the IDE keep track of which child widgets are available

    See ui_base_widget.j2, which is the jinja template for these output files.
    """
    # Parse the file
    ui_info = get_ui_info(designer_ui)

    # Bring the info into a good form for the jinja template
    ui_name = os.path.basename(designer_ui)
    base_cls = get_base_class_name(designer_ui=designer_ui)
    info_for_jinja = process_widget_macros(ui_info)

    macro_names = sorted(info_for_jinja.macro_set)
    widget_names = sorted(info_for_jinja.widget_set)

    # Fill the template
    jinja_template = "ui_base_widget.j2"
    env = Environment(trim_blocks=True, loader=PackageLoader("pcdswidgets", "builder"))
    template = env.get_template(jinja_template)
    jinja_output = template.render(
        jinja_template=jinja_template,
        ui_name=ui_name,
        form_cls=ui_info.form_cls,
        base_cls=base_cls,
        macro_names=macro_names,
        widget_names=widget_names,
        widget_name_to_class=ui_info.widget_name_to_class,
        macro_to_widget=info_for_jinja.macro_to_widget,
        widget_to_macro=info_for_jinja.widget_to_macro,
        widget_to_pre_templ_strs=info_for_jinja.widget_to_pre_templ_strs,
        widget_to_pre_templ_lists=info_for_jinja.widget_to_pre_templ_lists,
    )
    output_dir_path = get_output_path(designer_ui=designer_ui, default_base="generated", output_dir=output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)
    output_file = output_dir_path / os.path.basename(designer_ui).replace(".ui", "_base.py")
    with open(output_file, "w") as fd:
        fd.write(jinja_output)
    build_inits(base_dir=output_dir_path)


def build_main_widget(designer_ui: str, output_dir: str = ""):
    """
    Create a .py file that will be included in designer as-is.

    The files are named systematically with patterns like:
    some_name.ui -> some_name.py

    See ui_main_widget.j2, which is the jinja template for these output files.
    """
    # Collect some info
    designer_path = Path(designer_ui)
    module_parts = ["pcdswidgets"]
    seen_ui = False
    for path_part in designer_path.parts:
        if path_part == "ui":
            seen_ui = True
        elif seen_ui:
            module_parts.append(path_part)
    module_parts.append(os.path.basename(designer_ui).replace(".ui", "base"))
    absolute_import_path = ".".join(module_parts)
    group_parts = module_parts[1:-2]
    default_group = f"PCDS {' '.join(group_parts)}"
    # Fill the template
    jinja_template = "ui_main_widget.j2"
    env = Environment(trim_blocks=True, loader=PackageLoader("pcdswidgets", "builder"))
    template = env.get_template(jinja_template)
    jinja_output = template.render(
        absolute_import_path=absolute_import_path,
        base_cls=get_base_class_name(designer_ui=designer_ui),
        main_cls=get_main_class_name(designer_ui=designer_ui),
        default_group=default_group,
    )
    output_dir_path = get_output_path(designer_ui=designer_ui, default_base="", output_dir=output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)
    output_file = output_dir_path / os.path.basename(designer_ui).replace(".ui", ".py")
    with open(output_file, "w") as fd:
        fd.write(jinja_output)
    build_inits(base_dir=output_dir_path)


def build_inits(base_dir: str | Path):
    """
    Create blank __init__.py files wherever they are needed in generated directories.

    This makes Python treat these directories as Python modules.
    """
    candidates: set[Path] = set()
    base_dir = Path(base_dir)
    for path in base_dir.rglob("*"):
        if not path.name.startswith(".") and "__pycache__" not in path.parts:
            candidates.add(path.with_name("__init__.py"))
    for cand_path in candidates:
        cand_path.touch()


def get_output_path(designer_ui: str | Path, default_base: str, output_dir: str | Path = "") -> Path:
    if output_dir:
        return Path(output_dir)
    else:
        designer_ui_path = Path(designer_ui)
        designer_parts = list(designer_ui_path.parts)
        if default_base:
            for idx, part in enumerate(designer_parts):
                if part == "ui":
                    designer_parts[idx] = default_base
                    break
        else:
            designer_parts.remove("ui")
        return designer_ui_path.with_segments(*designer_parts[:-1])


def get_base_class_name(designer_ui: str) -> str:
    return get_main_class_name(designer_ui=designer_ui) + "Base"


def get_main_class_name(designer_ui: str):
    ui_name = os.path.basename(designer_ui)
    ui_parts = ui_name.removesuffix(".ui").split("_")
    return "".join(part.title() for part in ui_parts)


@dataclasses.dataclass
class UiInfo:
    """Information parsed from a .ui file."""

    widget_name_to_class: dict[str, str]
    widget_macros: dict[str, dict[str, str | list[str]]]
    form_cls: str


def get_ui_info(designer_ui: str) -> UiInfo:
    """Parse a .ui file and collect information about each widget."""
    # Need a name to class mapping for the IDE type hints
    widget_name_to_class: dict[str, str] = {}
    # Need to keep track of which widget properties have macros
    # widget_macros[widget_name][property_name] == "${MACRO} in context"
    widget_macros: dict[str, dict[str, str | list[str]]] = defaultdict(dict)

    tree = ET.parse(designer_ui)
    for widget in tree.iter("widget"):
        name = widget.attrib["name"]
        cls = widget.attrib["class"]
        widget_name_to_class[name] = cls
        for prop in widget.findall("property"):
            add_prop_to_widget_macros(widget_macros, name, prop)

    # Need to get the name of the form class, which is "Ui_" and the name of the top-level widget
    # Usually this ends up being "Ui_Form" with default naming but the user can change this
    top_level_widget = tree.find("widget")
    if top_level_widget is None:
        raise RuntimeError("No top level widget in ui file")
    form_cls = f"Ui_{top_level_widget.attrib['name']}"

    return UiInfo(
        widget_name_to_class=widget_name_to_class,
        widget_macros=widget_macros,
        form_cls=form_cls,
    )


def add_prop_to_widget_macros(widget_macros: defaultdict[str, dict[str, str | list[str]]], name: str, prop: ET.Element):
    """Incorporate a single property into the macros dict if there is a macro in it."""
    # Looking for string and stringlist only
    str_node = prop.find("string")
    if str_node is not None and str_node.text is not None:
        # We have simple text!
        if "${" in str_node.text:
            widget_macros[name][prop.attrib["name"]] = str_node.text
        return
    strlist_node = prop.find("stringlist")
    if strlist_node is not None:
        # We have a list of strings! Some may have macros.
        all_str_nodes = strlist_node.findall("string")
        all_str_literals = [node.text for node in all_str_nodes if node.text is not None]
        for text in all_str_literals:
            if "${" in text:
                widget_macros[name][prop.attrib["name"]] = all_str_literals
                return


@dataclasses.dataclass
class InfoForJinja:
    """Distilled widget and macro information for easily filling in the jinja template."""

    macro_set: set[str]
    widget_set: set[str]
    macro_to_widget: dict[str, list[str]]
    widget_to_macro: dict[str, list[str]]
    widget_to_pre_templ_strs: dict[str, list[tuple[str, str]]]
    widget_to_pre_templ_lists: dict[str, list[tuple[str, list[str]]]]


def process_widget_macros(ui_info: UiInfo) -> InfoForJinja:
    """Convert the raw ui info into a more useful form for filling the jinja template."""
    ij = InfoForJinja(
        macro_set=set(),
        widget_set=set(),
        macro_to_widget=defaultdict(list),
        widget_to_macro={},
        widget_to_pre_templ_strs=defaultdict(list),
        widget_to_pre_templ_lists=defaultdict(list),
    )

    for widget_name, prop_info in ui_info.widget_macros.items():
        macros_here = set()
        str_opts: list[tuple[str, str]] = []
        list_opts: list[tuple[str, list[str]]] = []
        for prop_name, value_with_macro in prop_info.items():
            if isinstance(value_with_macro, str):
                str_opts.append((prop_name, value_with_macro))
                macros_here.update(_get_macros(value_with_macro))
            elif isinstance(value_with_macro, list):
                list_opts.append((prop_name, value_with_macro))
                for val in value_with_macro:
                    macros_here.update(_get_macros(val))
            else:
                raise TypeError(f"Invalid macro type: {value_with_macro}")
        ij.macro_set.update(macros_here)
        ij.widget_set.add(widget_name)
        for macro in macros_here:
            ij.macro_to_widget[macro].append(widget_name)
        ij.widget_to_macro[widget_name] = sorted(macros_here)
        ij.widget_to_pre_templ_strs[widget_name].extend(str_opts)
        ij.widget_to_pre_templ_lists[widget_name].extend(list_opts)

    return ij


macro_re = re.compile(r"\${(\S+?)}")


def _get_macros(text_with_macro_sub: str) -> list[str]:
    """Helper for getting the name of each macro in use in a macro string."""
    return macro_re.findall(text_with_macro_sub)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        "pcdswidgets.builder.build",
        description="Automatically build the form or base class files associated with a widget .ui file.",
    )
    parser.add_argument(
        "mode",
        choices=["uic", "base", "main"],
        help=(
            "Choose 'uic' to build the pyuic form, "
            "'base' to build the pcdswidgets base class, "
            "or 'main' to build the pcdswidgets main (user editable) class."
        ),
    )
    parser.add_argument("designer_ui", help="Path to the designer .ui file to use as the source for the build.")
    args = parser.parse_args()

    if args.mode == "uic":
        build_uic(args.designer_ui)
    elif args.mode == "base":
        build_base_widget(args.designer_ui)
    elif args.mode == "main":
        build_main_widget(args.designer_ui)
    else:
        # Currently unreachable, probably
        raise ValueError(f"Invalid mode {args.mode}, must be uic, base, or main")
