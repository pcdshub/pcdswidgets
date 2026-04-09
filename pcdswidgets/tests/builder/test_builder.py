import importlib
import inspect
from pathlib import Path

import pytest

import pcdswidgets
from pcdswidgets.builder.designer_widget import DesignerWidget

UI_SOURCES = sorted((Path(pcdswidgets.__file__) / "ui").rglob("*.ui"))


@pytest.mark.parametrize("ui_source", UI_SOURCES)
def test_it_was_built(ui_source: Path):
    """
    Check if the current clone has had .py files built from all the source .ui files.
    """
    base_path = ui_source.parent / (ui_source.stem + "_base.py")
    form_path = ui_source.parent / (ui_source.stem + "_form.py")

    assert base_path.exists()
    assert form_path.exists()


@pytest.mark.parametrize("ui_source", UI_SOURCES)
def test_built_is_importable(ui_source: Path):
    """
    Check if the .py files in the current clone have somewhat proper importable classes.
    """
    base_module_name = "pcdswidgets.builder.ui." + ui_source.stem + "_base"
    form_module_name = "pcdswidgets.builder.ui." + ui_source.stem + "_form"

    base_module = importlib.import_module(base_module_name)
    form_module = importlib.import_module(form_module_name)

    base_classes = []
    for _, cls in inspect.getmembers(base_module, inspect.isclass):
        if inspect.getmodule(cls) is base_module:
            base_classes.append(cls)

    form_classes = []
    for _, cls in inspect.getmembers(form_module, inspect.isclass):
        if inspect.getmodule(cls) is form_module:
            form_classes.append(cls)

    assert len(base_classes) == 1
    assert issubclass(base_classes[0], DesignerWidget)

    assert len(form_classes) == 1
    assert hasattr(form_classes[0], "setupUi")
    assert hasattr(form_classes[0], "retranslateUi")
