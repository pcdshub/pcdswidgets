"""
Unit tests for TabDock and TabDockButton.
"""

from pathlib import Path
from unittest.mock import Mock

import pytest
from pytestqt.qtbot import QtBot

from pcdswidgets.common.dock.tab_dock import NoTabDockError, TabDock
from pcdswidgets.common.dock.tab_dock_button import TabDockButton

TESTS_DIR = Path(__file__).parent.resolve()


@pytest.fixture(scope="function")
def dock_button(qtbot: QtBot) -> TabDockButton:
    """Loads a TabDockButton"""
    button = TabDockButton()
    qtbot.addWidget(button)
    return button


@pytest.fixture(scope="function")
def tab_dock_mocks(monkeypatch: pytest.MonkeyPatch) -> dict[str, Mock]:
    """Applies mocks to TabDock"""
    mocks = {
        "add_to_dock_user_keybinds": Mock(),
        "show_widget_at_cursor": Mock(),
    }
    for name, mk in mocks.items():
        monkeypatch.setattr(TabDock, name, mk)
        monkeypatch.setattr(TabDock, name, mk)
    return mocks


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


def test_opens_in_dock_if_dock(dock_button: TabDockButton, tab_dock_mocks: dict[str, Mock]):
    dock_button.setFilename(str(TESTS_DIR / "dock1.ui"))
    tab_dock_mocks["add_to_dock_user_keybinds"].assert_not_called()
    tab_dock_mocks["show_widget_at_cursor"].assert_not_called()
    dock_button.open_in_dock()
    tab_dock_mocks["add_to_dock_user_keybinds"].assert_called_once()
    tab_dock_mocks["show_widget_at_cursor"].assert_not_called()


def test_opens_in_winow_if_no_dock(dock_button: TabDockButton, tab_dock_mocks: dict[str, Mock]):
    dock_button.setFilename(str(TESTS_DIR / "dock1.ui"))
    tab_dock_mocks["add_to_dock_user_keybinds"].side_effect = NoTabDockError
    tab_dock_mocks["show_widget_at_cursor"].assert_not_called()
    dock_button.open_in_dock()
    tab_dock_mocks["show_widget_at_cursor"].assert_called_once()
