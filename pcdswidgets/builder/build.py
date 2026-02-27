import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict

from jinja2 import Environment, PackageLoader


def build_uic(designer_ui: str):
    """
    Use the standard uic parser to create a .py file with a .ui file's widget layouts.

    The files are named systematically with patterns like:
    some_name.ui -> some_name_form.py
    """
    form_output = f"{os.path.splitext(designer_ui)[0]}_form.py"
    subprocess.run(f"pyuic5 -o {form_output} {designer_ui}".split(" "))


def build_base_widget(designer_ui: str):
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
    # Parse the .ui file and collect information about each widget
    # Need a name to class mapping for the IDE type hints
    widget_name_to_class: dict[str, str] = {}
    # Need to keep track of which widget properties have macros
    # widget_macros[widget_name][property_name] == "${MACRO} in context"
    widget_macros: dict[str, dict[str, str | list[str]]] = {}

    tree = ET.parse(designer_ui)
    for widget in tree.iter("widget"):
        name = widget.attrib["name"]
        cls = widget.attrib["class"]
        widget_name_to_class[name] = cls
        for prop in widget.findall("property"):
            # Looking for string and stringlist only
            str_node = prop.find("string")
            if str_node is not None and str_node.text is not None:
                # We have simple text!
                if "${" in str_node.text:
                    try:
                        widget_macros[name][prop.attrib["name"]] = str_node.text
                    except KeyError:
                        widget_macros[name] = {prop.attrib["name"]: str_node.text}
                continue
            strlist_node = prop.find("stringlist")
            if strlist_node is not None:
                # We have a list of strings! Some may have macros.
                all_str_nodes = strlist_node.findall("string")
                all_str_literals = [node.text for node in all_str_nodes if node.text is not None]
                for text in all_str_literals:
                    if "${" in text:
                        try:
                            widget_macros[name][prop.attrib["name"]] = all_str_literals
                        except KeyError:
                            widget_macros[name] = {prop.attrib["name"]: all_str_literals}

    # Need to get the name of the form class, which is "Ui_" and the name of the top-level widget
    # Usually this ends up being "Ui_Form" with default naming but the user can change this
    top_level_widget = tree.find("widget")
    if top_level_widget is None:
        raise RuntimeError("No top level widget in ui file")
    clsname = f"Ui_{top_level_widget.attrib["name"]}"

    # We're done parsing, now we bring the info into a good form for the jinja template
    ui_name = os.path.basename(designer_ui)
    macro_set: set[str] = set()
    widget_set: set[str] = set()
    macro_to_widget: dict[str, list[str]] = defaultdict(list)
    widget_to_macro: dict[str, list[str]] = {}
    widget_to_pre_templ_strs: dict[str, list[tuple[str, str]]] = defaultdict(list)
    widget_to_pre_templ_lists: dict[str, list[tuple[str, list[str]]]] = defaultdict(list)

    for widget_name, prop_info in widget_macros.items():
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
        macro_set.update(macros_here)
        widget_set.add(widget_name)
        for macro in macro_set:
            macro_to_widget[macro].append(widget_name)
        widget_to_macro[widget_name] = sorted(macros_here)
        widget_to_pre_templ_strs[widget_name].extend(str_opts)
        widget_to_pre_templ_lists[widget_name].extend(list_opts)

    macro_names = sorted(macro_set)
    widget_names = sorted(widget_set)

    # And last, standard jinja stuff
    jinja_template = "ui_base_widget.j2"
    env = Environment(trim_blocks=True, loader=PackageLoader("pcdswidgets", "builder"))
    template = env.get_template(jinja_template)
    jinja_output = template.render(
        jinja_template=jinja_template,
        ui_name=ui_name,
        clsname=clsname,
        macro_names=macro_names,
        widget_names=widget_names,
        widget_name_to_class=widget_name_to_class,
        macro_to_widget=macro_to_widget,
        widget_to_macro=widget_to_macro,
        widget_to_pre_templ_strs=widget_to_pre_templ_strs,
        widget_to_pre_templ_lists=widget_to_pre_templ_lists,
    )
    dst_path = designer_ui.removesuffix(".ui") + "_base.py"
    with open(dst_path, "w") as fd:
        fd.write(jinja_output)


macro_re = re.compile(r"\${(\S+)}")


def _get_macros(text_with_macro_sub: str) -> list[str]:
    return macro_re.findall(text_with_macro_sub)


if __name__ == "__main__":
    print(sys.argv)
    designer_ui = sys.argv[1]
    build_uic(designer_ui)
    build_base_widget(designer_ui)
