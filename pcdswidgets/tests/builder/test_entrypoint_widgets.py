from importlib.metadata import entry_points

import pytest
from pydm.config import ENTRYPOINT_WIDGET
from qtpy.QtWidgets import QWidget

from pcdswidgets.builder.entrypoint_finder import get_widget_entrypoint_data, iter_all_widgets


def test_entrypoint_has_all_widgets():
    """
    Ensure that all widgets are included in designer via the pydm designer plugin.

    If this fails, but test_toml_has_all_widgets is passing, it's likely because
    pcdswidgets is not installed in dev mode.
    """
    pydm_widgets = entry_points(group=ENTRYPOINT_WIDGET)
    name_and_entrypoint = get_widget_entrypoint_data()
    for name, entrypoint in name_and_entrypoint:
        assert pydm_widgets.select(name=name)[name].value == entrypoint


container_widgets = [
    "FilterSortWidgetTable",
]

# Don't check widgets from before we made sizing/naming standards
exempt_widgets = [
    "ApertureValve",
    "CapacitanceManometerGauge",
    "ColdCathodeComboGauge",
    "ColdCathodeGauge",
    "ControlOnlyValveNC",
    "ControlOnlyValveNO",
    "ControlValve",
    "EPSByteIndicator",
    "FastShutter",
    "GetterPump",
    "HotCathodeComboGauge",
    "HotCathodeGauge",
    "IonPump",
    "NeedleValve",
    "PneumaticValve",
    "PneumaticValveDA",
    "PneumaticValveNO",
    "ProportionalValve",
    "RGA",
    "RightAngleManualValve",
    "RoughGauge",
    "ScrollPump",
    "TurboPump",
] + container_widgets


@pytest.mark.parametrize(
    "widget_name,WidgetCls", [elem for elem in iter_all_widgets() if elem[0] not in exempt_widgets]
)
def test_widget_sizing(widget_name: str, WidgetCls: type[QWidget], qtbot):
    """
    Ensure that all widgets are named and sized appropriately as per our standards.
    """
    widget = WidgetCls()
    qtbot.addWidget(widget)
    # 20% smaller is OK
    ratio = 0.8

    if widget_name.endswith("Full"):
        max_w = 400
        max_h = 125
        min_w = ratio * max_w
        min_h = ratio * max_h
    elif widget_name.endswith("Compact"):
        max_w = 100
        max_h = 75
        min_w = ratio * max_w
        min_h = ratio * max_h
    elif widget_name.endswith("Row"):
        max_w = 800
        max_h = 50
        min_w = ratio * max_w
        min_h = ratio * max_h
        # Allow double rows
        max_h = max_h * 2
    else:
        raise ValueError(
            f"Widget named {widget_name} does not follow naming convention: "
            "must end with Full, Compact, or Row to signal size class."
        )

    assert widget.minimumWidth() >= min_w, f"{widget_name}'s minimum width is too small."
    assert widget.maximumWidth() <= max_w, f"{widget_name}'s maximum width is too large."
    assert widget.minimumHeight() >= min_h, f"{widget_name}'s minimum height is too small."
    assert widget.maximumHeight() <= max_h, f"{widget_name}'s maximum height is too large."


@pytest.mark.parametrize("widget_name,WidgetCls", [elem for elem in iter_all_widgets() if elem[0] in container_widgets])
def test_container_widget_sizing(widget_name: str, WidgetCls: type[QWidget], qtbot):
    """
    Ensure that container widgets have no maximum size.
    """
    widget = WidgetCls()
    qtbot.addWidget(widget)

    # The max size is currently 16777215
    # Pick a smaller but still absurd number as the threshold
    assert widget.maximumWidth() >= 100000, f"{widget_name}'s maximum width is too small."
    assert widget.maximumHeight() >= 100000, f"{widget_name}'s maximum height is too small."
