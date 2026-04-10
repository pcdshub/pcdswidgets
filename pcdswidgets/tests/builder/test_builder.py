import importlib
import inspect
from pathlib import Path

import pytest

import pcdswidgets
from pcdswidgets.builder.designer_widget import DesignerWidget

MODULE_ROOT = Path(pcdswidgets.__file__).parent
UI_SOURCES = sorted((MODULE_ROOT / "ui").rglob("*.ui"))

TEST_UI = str(Path(__file__).parent / "pytest.ui")


@pytest.mark.parametrize("ui_source", UI_SOURCES)
def test_it_was_built(ui_source: Path):
    """
    Check if .py files have been built from all the source .ui files.
    """
    subsystem, device = get_subsystem_and_device(ui_source=ui_source)

    gen_dir = MODULE_ROOT / "generated" / subsystem / device
    base_path = gen_dir / (ui_source.stem + "_base.py")
    form_path = gen_dir / (ui_source.stem + "_form.py")

    main_path = MODULE_ROOT / subsystem / device / (ui_source.stem + ".py")

    assert base_path.exists()
    assert form_path.exists()
    assert main_path.exists()


def get_subsystem_and_device(ui_source: Path) -> tuple[str, str]:
    subsystem = None
    device = None

    seen_ui = False
    for part in ui_source.parts:
        if part == "ui":
            seen_ui = True
        elif seen_ui:
            if subsystem is None:
                subsystem = part
            else:
                device = part
                break

    assert subsystem is not None
    assert device is not None

    return subsystem, device


@pytest.mark.parametrize("ui_source", UI_SOURCES)
def test_built_is_importable(ui_source: Path):
    """
    Check if the .py files have somewhat proper importable classes.
    """
    subsystem, device = get_subsystem_and_device(ui_source=ui_source)

    form_module_name = f"pcdswidgets.generated.{subsystem}.{device}.{ui_source.stem}_form"
    base_module_name = f"pcdswidgets.generated.{subsystem}.{device}.{ui_source.stem}_base"
    main_module_name = f"pcdswidgets.{subsystem}.{device}.{ui_source.stem}"

    form_module = importlib.import_module(form_module_name)
    base_module = importlib.import_module(base_module_name)
    main_module = importlib.import_module(main_module_name)

    form_classes = []
    for _, cls in inspect.getmembers(form_module, inspect.isclass):
        if inspect.getmodule(cls) is form_module:
            form_classes.append(cls)

    base_classes = []
    for _, cls in inspect.getmembers(base_module, inspect.isclass):
        if inspect.getmodule(cls) is base_module:
            base_classes.append(cls)

    main_classes = []
    for _, cls in inspect.getmembers(main_module, inspect.isclass):
        if inspect.getmodule(cls) is main_module:
            main_classes.append(cls)

    assert len(form_classes) == 1
    assert hasattr(form_classes[0], "setupUi")
    assert hasattr(form_classes[0], "retranslateUi")

    assert len(base_classes) == 1
    assert issubclass(base_classes[0], DesignerWidget)
    assert base_classes[0].ui_form is form_classes[0]

    assert len(main_classes) == 1
    assert hasattr(main_classes[0], "designer_options")
    assert hasattr(main_classes[0], "_qt_designer_")
    assert issubclass(main_classes[0], base_classes[0])
