"""
Unit tests for TabDock and TabDockButton.
"""

from pathlib import Path
from unittest.mock import Mock

import pytest
from pytestqt.qtbot import QtBot
from qtpy.QtGui import QCursor
from qtpy.QtWidgets import QWidget

import pcdswidgets.common.dock.tab_dock as dock_module
from pcdswidgets.common.dock.tab_dock import TabDock

TESTS_DIR = Path(__file__).parent.resolve()


def test_add_to_dock_user_keybinds(tab_dock: TabDock, monkeypatch: pytest.MonkeyPatch, qtbot: QtBot):
    # Mock our own methods to check if they got called
    add_to_dock_mock = Mock()
    open_in_new_window_mock = Mock()
    monkeypatch.setattr(TabDock, "add_to_dock", add_to_dock_mock)
    monkeypatch.setattr(TabDock, "open_in_new_window", open_in_new_window_mock)

    def reset_mocks():
        add_to_dock_mock.reset_mock()
        open_in_new_window_mock.reset_mock()

    title = "title"
    widget = QWidget()
    qtbot.addWidget(widget)

    def add_to_dock():
        TabDock.add_to_dock_user_keybinds(title=title, widget=widget)

    # Standard: open in dock
    reset_mocks()
    add_to_dock()
    add_to_dock_mock.assert_called_once_with(title=title, widget=widget, new_tab=False)
    open_in_new_window_mock.assert_not_called()

    # Dock hidden: open in new window
    reset_mocks()
    tab_dock.hide()
    add_to_dock()
    add_to_dock_mock.assert_not_called()
    open_in_new_window_mock.assert_called_once_with(title=title, widget=widget)
    tab_dock.show()

    # Ctrl pressed: open in dock in a new tab
    monkeypatch.setattr(dock_module, "ctrl_pressed", lambda: True)
    monkeypatch.setattr(dock_module, "shift_pressed", lambda: False)
    reset_mocks()
    add_to_dock()
    add_to_dock_mock.assert_called_once_with(title=title, widget=widget, new_tab=True)
    open_in_new_window_mock.assert_not_called()

    # Shift pressed: open in new window
    monkeypatch.setattr(dock_module, "ctrl_pressed", lambda: False)
    monkeypatch.setattr(dock_module, "shift_pressed", lambda: True)
    reset_mocks()
    add_to_dock()
    add_to_dock_mock.assert_not_called()
    open_in_new_window_mock.assert_called_once_with(title=title, widget=widget)


def test_add_to_dock(tab_dock: TabDock, qtbot: QtBot):
    widget1 = QWidget()
    qtbot.add_widget(widget1)
    widget2 = QWidget()
    qtbot.add_widget(widget2)

    tab_widget = tab_dock.tab_widgets[0][0]

    TabDock.add_to_dock(title="", widget=widget1)
    assert tab_widget.currentWidget() is widget1
    assert tab_widget.count() == 1

    TabDock.add_to_dock(title="", widget=widget2)
    assert tab_widget.currentWidget() is widget2
    assert tab_widget.count() == 1

    TabDock.add_to_dock(title="", widget=widget1, new_tab=True)
    assert tab_widget.currentWidget() is widget1
    assert tab_widget.count() == 2


def test_detach_from_dock(tab_dock: TabDock, qtbot: QtBot):
    widget1 = QWidget()
    qtbot.add_widget(widget1)

    tab_widget = tab_dock.tab_widgets[0][0]

    tab_dock.add_to_dock(title="", widget=widget1)
    tab_dock.detach_from_dock(tab_widget=tab_widget)

    assert tab_widget.currentWidget() is None
    assert tab_widget.count() == 0

    assert widget1.parent() is None
    assert widget1.isVisible()
    assert widget1 in tab_dock.detached_widgets


def test_open_in_new_window(tab_dock: TabDock, qtbot: QtBot):
    widget1 = QWidget()
    qtbot.add_widget(widget1)

    TabDock.open_in_new_window(title="", widget=widget1)

    tab_widget = tab_dock.tab_widgets[0][0]

    assert tab_widget.currentWidget() is None
    assert tab_widget.count() == 0

    assert widget1.parent() is None
    assert widget1.isVisible()
    assert widget1 in tab_dock.detached_widgets


def test_reattach_user_choice(tab_dock: TabDock, monkeypatch: pytest.MonkeyPatch, qtbot: QtBot):
    # Mock our own methods to check if they got called
    reattach_to_dock_mock = Mock()
    show_attach_menu_mock = Mock()
    monkeypatch.setattr(TabDock, "reattach_to_dock", reattach_to_dock_mock)
    monkeypatch.setattr(TabDock, "show_attach_menu", show_attach_menu_mock)

    tab_widget = tab_dock.tab_widgets[0][0]

    def reset_mocks():
        reattach_to_dock_mock.reset_mock()
        show_attach_menu_mock.reset_mock()

    reset_mocks()
    tab_dock.reattach_user_choice(tab_widget=tab_widget)
    reattach_to_dock_mock.assert_not_called()
    show_attach_menu_mock.assert_not_called()

    widget1 = QWidget()
    qtbot.add_widget(widget1)

    TabDock.open_in_new_window(title="", widget=widget1)
    reset_mocks()
    tab_dock.reattach_user_choice(tab_widget=tab_widget)
    reattach_to_dock_mock.assert_called_once_with(widget=widget1, tab_widget=tab_widget)
    show_attach_menu_mock.assert_not_called()

    widget2 = QWidget()
    qtbot.add_widget(widget2)

    TabDock.open_in_new_window(title="", widget=widget2)
    reset_mocks()
    tab_dock.reattach_user_choice(tab_widget=tab_widget)
    reattach_to_dock_mock.assert_not_called()
    show_attach_menu_mock.assert_called_once_with(tab_widget=tab_widget, pos=QCursor().pos())


def test_reattach_to_dock(tab_dock: TabDock, qtbot: QtBot):
    widget1 = QWidget()
    qtbot.add_widget(widget1)

    tab_widget = tab_dock.tab_widgets[0][0]

    TabDock.open_in_new_window(title="", widget=widget1)
    tab_dock.reattach_to_dock(widget=widget1, tab_widget=tab_widget)

    assert widget1 not in tab_dock.detached_widgets
    assert tab_widget.currentWidget() is widget1
    assert tab_widget.count() == 1

    widget2 = QWidget()
    qtbot.add_widget(widget2)

    TabDock.open_in_new_window(title="", widget=widget2)
    tab_dock.reattach_to_dock(widget=widget2, tab_widget=tab_widget)

    assert widget2 not in tab_dock.detached_widgets
    assert tab_widget.currentWidget() is widget2
    assert tab_widget.count() == 2


def test_show_attach_menu(tab_dock: TabDock, qtbot: QtBot):
    tab_widget = tab_dock.tab_widgets[0][0]

    widgets = [QWidget() for _ in range(3)]
    for num, wd in enumerate(widgets):
        qtbot.add_widget(wd)
        TabDock.open_in_new_window(title=f"{num}", widget=wd)
        assert wd in tab_dock.detached_widgets

    menu = tab_dock.show_attach_menu(tab_widget=tab_widget)
    for action in menu.actions():
        action.trigger()
        this_widget = widgets[int(action.text())]
        qtbot.wait_signal(action.triggered)
        assert this_widget not in tab_dock.detached_widgets
        assert tab_widget.currentWidget() is this_widget

    assert tab_widget.count() == 3


def test_clean_detached_widgets(tab_dock: TabDock, qtbot: QtBot):
    widget1 = QWidget()
    qtbot.add_widget(widget1)

    TabDock.open_in_new_window(title="", widget=widget1)
    assert widget1 in tab_dock.detached_widgets

    widget1.close()

    def not_vis():
        assert not widget1.isVisible()

    qtbot.wait_until(not_vis)

    tab_dock.clean_detached_widgets()
    assert not tab_dock.detached_widgets


def test_not_clean_minimized_widgets(tab_dock: TabDock, qtbot: QtBot):
    widget1 = QWidget()
    qtbot.add_widget(widget1)

    TabDock.open_in_new_window(title="", widget=widget1)
    assert widget1 in tab_dock.detached_widgets

    widget1.showMinimized()

    def is_minim():
        assert widget1.isMinimized()

    qtbot.wait_until(is_minim)

    tab_dock.clean_detached_widgets()
    assert widget1 in tab_dock.detached_widgets


def test_multidock(tab_dock: TabDock, qtbot: QtBot):
    widgets = [QWidget() for _ in range(7)]
    for widget in widgets:
        qtbot.add_widget(widget)

    tab_dock.dock_columns_spinbox.setValue(3)
    tab_dock.dock_rows_spinbox.setValue(2)
    tab_dock.apply_settings()

    # 6 docks, we should fill them in order and then replace the first one
    tab_dock.add_to_dock(widgets[0], "")
    assert tab_dock.tab_widgets[0][0].currentWidget() is widgets[0]
    tab_dock.add_to_dock(widgets[1], "")
    assert tab_dock.tab_widgets[0][1].currentWidget() is widgets[1]
    tab_dock.add_to_dock(widgets[2], "")
    assert tab_dock.tab_widgets[0][2].currentWidget() is widgets[2]
    tab_dock.add_to_dock(widgets[3], "")
    assert tab_dock.tab_widgets[1][0].currentWidget() is widgets[3]
    tab_dock.add_to_dock(widgets[4], "")
    assert tab_dock.tab_widgets[1][1].currentWidget() is widgets[4]
    tab_dock.add_to_dock(widgets[5], "")
    assert tab_dock.tab_widgets[1][2].currentWidget() is widgets[5]
    tab_dock.add_to_dock(widgets[6], "")
    assert tab_dock.tab_widgets[0][0].currentWidget() is widgets[6]

    # We should be able to move a widget from dock 2 to dock 4
    assert widgets[1] not in tab_dock.detached_widgets
    tab_dock.detach_from_dock(tab_dock.tab_widgets[0][1])
    assert widgets[1] in tab_dock.detached_widgets
    assert tab_dock.tab_widgets[0][1].currentWidget() is not widgets[1]
    tab_dock.reattach_to_dock(widgets[1], tab_dock.tab_widgets[1][1])
    assert widgets[1] not in tab_dock.detached_widgets
    assert tab_dock.tab_widgets[1][1].currentWidget() is widgets[1]
