"""Create the uic, base, and main .py files from the input .ui files."""

import argparse
import os
from io import StringIO
from pathlib import Path

from jinja2 import Environment, PackageLoader
from qtpy.uic import compileUi  # type: ignore

from .read_ui import get_ui_info, process_widget_macros


def build_uic(designer_ui: str, output_dir: str = ""):
    """
    Use the standard uic parser to create a .py file with a .ui file's widget layouts.

    The files are named systematically with patterns like:
    some_name.ui -> some_name_form.py
    """
    string_io = StringIO()
    compileUi(designer_ui, string_io)

    comment_lines = []
    import_lines = []
    impl_lines = []

    for line in string_io.getvalue().split("\n"):
        if line.startswith("from"):
            import_lines.append(line.replace("PyQt5", "qtpy"))
            continue
        if import_lines:
            if "${" not in line:
                impl_lines.append(line)
            elif impl_lines[-1].isspace():
                del impl_lines[-1]
        elif line:
            comment_lines.append(line)

    comment_lines.append("#")
    comment_lines.append("# Augmented by pcdswidgets.builder.build")
    comment_lines.append("# ruff: noqa: E501")

    output_dir_path = get_output_path(designer_ui=designer_ui, default_base="generated", output_dir=output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)
    output_file = output_dir_path / os.path.basename(designer_ui).replace(".ui", "_form.py")
    with open(output_file, "w") as fd:
        fd.writelines(cl + "\n" for cl in comment_lines)
        fd.writelines(il + "\n" for il in import_lines)
        fd.writelines(impl + "\n" for impl in impl_lines)


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
    all_widget_names = sorted(info_for_jinja.all_widget_set)
    macro_widget_names = sorted(info_for_jinja.macro_widget_set)

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
        all_widget_names=all_widget_names,
        macro_widget_names=macro_widget_names,
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


def build_main_widget(designer_ui: str, output_dir: str = ""):
    """
    Create a .py file that will be included in designer as-is.

    The files are named systematically with patterns like:
    some_name.ui -> some_name.py

    See ui_main_widget.j2, which is the jinja template for these output files.
    """
    # Collect some info
    designer_path = Path(designer_ui)
    module_parts = ["pcdswidgets", "generated"]
    seen_ui = False
    for path_part in designer_path.parts[:-1]:
        if path_part == "ui":
            seen_ui = True
        elif seen_ui:
            module_parts.append(path_part)
    module_parts.append(os.path.basename(designer_ui).replace(".ui", "_base"))
    absolute_import_path = ".".join(module_parts)
    default_group = f"ECS {module_parts[2].title()} {module_parts[3].title()}"
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
        fd.write(jinja_output + "\n")


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
