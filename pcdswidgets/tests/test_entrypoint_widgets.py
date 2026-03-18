from importlib.metadata import entry_points

import pytest
from pydm.config import ENTRYPOINT_WIDGET
from qtpy.QtWidgets import QWidget

from pcdswidgets.entrypoint_widgets import get_widget_entrypoint_data, iter_all_widgets


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
    "FilterSortWidgetTable",
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
]


@pytest.mark.parametrize(
    "widget_name,WidgetCls", [elem for elem in iter_all_widgets() if elem[0] not in exempt_widgets]
)
def test_widget_sizing(widget_name: str, WidgetCls: type[QWidget], qtbot):
    """
    Ensure that all widgets are named and sized appropriately as per our standards.
    """
    widget = WidgetCls()
    qtbot.addWidget(widget)

    if widget_name.endswith("Full"):
        max_w = 250
        max_h = 120
        min_w = 0.9 * max_w
        min_h = 0.9 * max_h
    elif widget_name.endswith("Compact"):
        max_w = 75
        max_h = 75
        min_w = 0.9 * max_w
        min_h = 0.9 * max_h
    elif widget_name.endswith("Row"):
        max_w = 680
        max_h = 40
        min_w = 0.9 * max_w
        min_h = 0.9 * max_h
    else:
        raise ValueError(
            f"Widget named {widget_name} does not follow naming convention: "
            "must end with Full, Compact, or Row to signal size class."
        )

    assert min_w <= widget.minimumWidth() <= widget.maximumWidth() <= max_w
    assert min_h <= widget.minimumHeight() <= widget.maximumHeight() <= max_h
