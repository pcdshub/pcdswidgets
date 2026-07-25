"""
Unit tests for the IndicatorGrid.

Note that I've done some strange things here to step around type linters,
which are very concerned about the ways SynAxis, motor, and Device types
in general are being carelessly thrown around here.

Type annotations are left off intentionally in many methods below as part
of this.
"""

import pytest
from pytestqt.qtbot import QtBot
from qtpy.QtWidgets import QWidget

from pcdswidgets.common.dock.indicator_grid import IndicatorCell

try:
    from ophyd.sim import SynAxis, motor  # type: ignore

    no_ophyd = False
except ImportError:
    from types import SimpleNamespace

    # Make the type linter less sad
    SynAxis = SimpleNamespace
    motor = SimpleNamespace()
    no_ophyd = True

SKIP_REASON = "Test requires ophyd, not installed."


@pytest.fixture(scope="function")
def cell(qtbot: QtBot) -> IndicatorCell:
    cell = IndicatorCell()
    qtbot.addWidget(cell)
    return cell


@pytest.mark.skipif(no_ophyd, reason=SKIP_REASON)
def test_base_device_button_menu(cell, tab_dock):
    device_count = 12
    for i in range(device_count):
        motor = SynAxis(name=f"motor_{i}")
        cell.add_device(motor)
    cell._menu_shown()
    for device in cell.devices:
        assert device.name in [action.text() for action in cell.device_menu.actions()]


@pytest.mark.skipif(no_ophyd, reason=SKIP_REASON)
def test_base_device_button_show_device(cell):
    display = cell.show_device(motor)
    assert display.devices[0] == motor
    assert motor.name in cell._device_displays


@pytest.mark.skipif(no_ophyd, reason=SKIP_REASON)
def test_base_device_button_show_device_repeated(cell, qtbot):
    widget = QWidget()
    qtbot.addWidget(widget)
    cell._device_displays[motor.name] = widget
    cell.show_device(motor)
    assert cell._device_displays[motor.name] == widget


@pytest.mark.skipif(no_ophyd, reason=SKIP_REASON)
def test_base_device_button_show_all(cell):
    cell.devices = [motor]
    screens = cell.show_all()
    assert [sc.devices[0] for sc in screens] == [motor]


@pytest.mark.skipif(no_ophyd, reason=SKIP_REASON)
def test_base_device_button_show_all_repeated(cell):
    cell.devices = [motor]
    screens1 = cell.show_all()
    screens2 = cell.show_all()
    assert screens1 == screens2
    assert [sc.devices[0] for sc in screens1] == [motor]


@pytest.mark.skipif(no_ophyd, reason=SKIP_REASON)
def test_indicator_cell_add_device(cell):
    device_count = 12
    for i in range(device_count):
        motor = SynAxis(name=f"motor_{i}")
        cell.add_device(motor)
    assert len(cell.devices) == 12
