"""Define functions for reading ui files an extracting information from them."""

import dataclasses
import re
import xml.etree.ElementTree as ET
from collections import defaultdict

from qtpy import QtWidgets


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
        if hasattr(QtWidgets, cls):
            clsname_text = f"QtWidgets.{cls}"
        else:
            clsname_text = cls
        widget_name_to_class[name] = clsname_text
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
        all_str_literals = []
        for node in all_str_nodes:
            if node.text is None:
                all_str_literals.append("")
            else:
                all_str_literals.append(node.text)
        for text in all_str_literals:
            if "${" in text:
                widget_macros[name][prop.attrib["name"]] = all_str_literals
                return


@dataclasses.dataclass
class InfoForJinja:
    """Distilled widget and macro information for easily filling in the jinja template."""

    macro_set: set[str]
    all_widget_set: set[str]
    macro_widget_set: set[str]
    macro_to_widget: dict[str, list[str]]
    widget_to_macro: dict[str, list[str]]
    widget_to_pre_templ_strs: dict[str, list[tuple[str, str]]]
    widget_to_pre_templ_lists: dict[str, list[tuple[str, list[str]]]]


def process_widget_macros(ui_info: UiInfo) -> InfoForJinja:
    """Convert the raw ui info into a more useful form for filling the jinja template."""
    ij = InfoForJinja(
        macro_set=set(),
        all_widget_set=set(),
        macro_widget_set=set(),
        macro_to_widget=defaultdict(list),
        widget_to_macro={},
        widget_to_pre_templ_strs=defaultdict(list),
        widget_to_pre_templ_lists=defaultdict(list),
    )
    for widget_name in ui_info.widget_name_to_class:
        ij.all_widget_set.add(widget_name)

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
        ij.macro_widget_set.add(widget_name)
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
