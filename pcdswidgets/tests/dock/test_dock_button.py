"""
Unit tests for TabDock and TabDockButton.
"""

from pathlib import Path

import pytest
from pytestqt.qtbot import QtBot

from pcdswidgets.common.dock.tab_dock_button import TabDockButton

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
