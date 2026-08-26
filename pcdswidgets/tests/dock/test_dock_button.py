"""
Unit tests for TabDock and TabDockButton.
"""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from pytestqt.qtbot import QtBot

from pcdswidgets.common.dock.tab_dock import TabDock
from pcdswidgets.common.dock.tab_dock_button import ScreenSource, TabDockButton

TESTS_DIR = Path(__file__).parent.resolve()


@pytest.fixture(scope="function")
def dock_button(qtbot: QtBot) -> TabDockButton:
    """Loads a TabDockButton"""
    button = TabDockButton()
    qtbot.addWidget(button)
    return button


@pytest.fixture(scope="function")
def tab_button_mocks(dock_button: TabDockButton, monkeypatch: pytest.MonkeyPatch) -> dict[str, Mock]:
    """Applies mocks to TabDock"""
    mocks = {"open_in_dock": Mock(), "open_in_window": Mock(), "open_menu": Mock()}
    for name, mk in mocks.items():
        monkeypatch.setattr(dock_button, name, mk)
    return mocks


def test_build_widget(dock_button: TabDockButton):
    """When we build a widget, it should match the file."""
    dock_button.setFilename(str(TESTS_DIR / "dock1.ui"))
    widget1 = dock_button.build_widget()
    assert widget1.windowTitle() == "DOCK1"
    widget2 = dock_button.build_widget()
    assert widget1 is widget2


def test_build_widget_ui_edited(dock_button: TabDockButton, tmp_path: Path):
    """We should rebuild the widget only if the file has changed."""
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
    """We should also be able to build widgets from internal pcdswidget screen names."""
    dock_button.setSource(ScreenSource.SCREEN_NAME)
    dock_button.setFilename("VVC_expert")
    widget1 = dock_button.build_widget()
    widget2 = dock_button.build_widget()
    assert widget2 is widget1


def test_build_widget_widget_name(dock_button: TabDockButton):
    """We should also be able to build widgets from internal pcdswidget widget types."""
    dock_button.setSource(ScreenSource.WIDGET_NAME)
    dock_button.setFilename("FeatureFinder")
    dock_button.setMacro('{"detector": "test_det", "motor": "test_mot"}')
    widget1 = dock_button.build_widget()
    assert widget1.property("detector") == "test_det"
    assert widget1.property("motor") == "test_mot"
    widget2 = dock_button.build_widget()
    assert widget2 is widget1


def test_opens_in_dock_if_dock(tab_dock: TabDock, dock_button: TabDockButton, tab_button_mocks: dict[str, Mock]):
    """When the user clicks the button, if there is a dock we should open in the dock."""
    tab_button_mocks["open_in_dock"].assert_not_called()
    tab_button_mocks["open_in_window"].assert_not_called()
    tab_button_mocks["open_menu"].assert_not_called()

    dock_button.open_widget()

    tab_button_mocks["open_in_dock"].assert_called_once()
    tab_button_mocks["open_in_window"].assert_not_called()
    tab_button_mocks["open_menu"].assert_not_called()


def test_opens_in_winow_if_no_dock(dock_button: TabDockButton, tab_button_mocks: dict[str, Mock]):
    """When the user clicks the button, if there is no dock we should open in a window."""
    TabDock.clear_instance()

    tab_button_mocks["open_in_dock"].assert_not_called()
    tab_button_mocks["open_in_window"].assert_not_called()
    tab_button_mocks["open_menu"].assert_not_called()

    dock_button.open_widget()

    tab_button_mocks["open_in_dock"].assert_not_called()
    tab_button_mocks["open_in_window"].assert_called_once()
    tab_button_mocks["open_menu"].assert_not_called()


def test_opens_menu_if_dock(tab_dock: TabDock, dock_button: TabDockButton, tab_button_mocks: dict[str, Mock]):
    """When the user right-clicks the button, if there is a dock we should open a menu."""
    tab_button_mocks["open_in_dock"].assert_not_called()
    tab_button_mocks["open_in_window"].assert_not_called()
    tab_button_mocks["open_menu"].assert_not_called()

    dock_button.contextMenuEvent(event=SimpleNamespace(globalPos=Mock()))  # type: ignore

    tab_button_mocks["open_in_dock"].assert_not_called()
    tab_button_mocks["open_in_window"].assert_not_called()
    tab_button_mocks["open_menu"].assert_called_once()


def test_skip_menu_if_no_dock(dock_button: TabDockButton, tab_button_mocks: dict[str, Mock]):
    """When the user right-clicks the button, if there is no dock we should open a window."""
    TabDock.clear_instance()

    tab_button_mocks["open_in_dock"].assert_not_called()
    tab_button_mocks["open_in_window"].assert_not_called()
    tab_button_mocks["open_menu"].assert_not_called()

    dock_button.contextMenuEvent(event=SimpleNamespace(globalPos=Mock()))  # type: ignore

    tab_button_mocks["open_in_dock"].assert_not_called()
    tab_button_mocks["open_in_window"].assert_called_once()
    tab_button_mocks["open_menu"].assert_not_called()
