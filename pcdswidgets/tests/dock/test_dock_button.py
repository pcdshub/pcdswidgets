"""
Unit tests for TabDock and TabDockButton.
"""

from pathlib import Path

import pytest
from pytestqt.qtbot import QtBot

from pcdswidgets.common.dock.tab_dock_button import ScreenSource, TabDockButton

TESTS_DIR = Path(__file__).parent.resolve()


@pytest.fixture(scope="function")
def dock_button(qtbot: QtBot) -> TabDockButton:
    button = TabDockButton()
    qtbot.addWidget(button)
    return button


def test_build_widget(dock_button: TabDockButton):
    dock_button.setFilename(str(TESTS_DIR / "dock1.ui"))
    widget1 = dock_button.build_widget()
    assert widget1.windowTitle() == "DOCK1"
    widget2 = dock_button.build_widget()
    assert widget1 is widget2


def test_build_widget_ui_edited(dock_button: TabDockButton, tmp_path: Path):
    local_ui = TESTS_DIR / "dock1.ui"
    temp_ui = tmp_path / "dock1.ui"

    with open(local_ui, "r") as fd:
        original_text = fd.read()

    with open(temp_ui, "w") as fd:
        fd.write(original_text)

    dock_button.setFilename(str(temp_ui))
    widget1 = dock_button.build_widget()
    assert widget1.windowTitle() == "DOCK1"

    new_text = original_text.replace("DOCK1", "NEW_EDIT")

    with open(temp_ui, "w") as fd:
        fd.write(new_text)

    widget2 = dock_button.build_widget()
    assert widget1 is not widget2
    assert widget2.windowTitle() == "NEW_EDIT"


def test_build_widget_screen_name(dock_button: TabDockButton):
    dock_button.setSource(ScreenSource.SCREEN_NAME)
    dock_button.setFilename("VVC_expert")
    widget1 = dock_button.build_widget()
    widget2 = dock_button.build_widget()
    assert widget2 is widget1


def test_build_widget_widget_name(dock_button: TabDockButton):
    dock_button.setSource(ScreenSource.WIDGET_NAME)
    dock_button.setFilename("FeatureFinder")
    dock_button.setMacro('{"detector": "test_det", "motor": "test_mot"}')
    widget1 = dock_button.build_widget()
    assert widget1.property("detector") == "test_det"
    assert widget1.property("motor") == "test_mot"
    widget2 = dock_button.build_widget()
    assert widget2 is widget1
