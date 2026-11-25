"""
Connection lifecycle of the EtherCAT widgets: PV subscriptions are shared, not duplicated,
and released when a widget is deleted (also without a closeEvent, e.g. embedded in a screen).

Offline: :data:`conftest.OFFLINE` records which channels are open.
"""

from pytestqt.qtbot import QtBot
from qtpy import QtCore

from pcdswidgets.common.ethercat.ethercat_terminal_state_double_row import EthercatTerminalStateDoubleRow

from .conftest import OFFLINE, PREFIX, make_states, select, wait


def delete_now(widget):
    """deleteLater() and run the deferred delete (processEvents() alone does not)."""
    widget.deleteLater()
    QtCore.QCoreApplication.sendPostedEvents(None, QtCore.QEvent.DeferredDelete)
    wait(0.1)


def panel_channels(panel) -> list:
    """Channels of the panel's own PyDM widgets (State_RBV label, State_SP combo)."""
    return [*(panel.PyDMLabel_rbv.channels() or []), *(panel.PyDMEnumComboBox_state.channels() or [])]


def test_panel_shares_the_tree_monitor(states):
    w = select(states, 1020)
    assert w.monitor is states.monitors[1020]  # no second subscription for the selection
    assert w._owned == []
    select(states, 1001)
    assert w.monitor is states.monitors[1001]
    assert all(OFFLINE.is_open(c) for c in states.monitors[1020].channels), "switching keeps the tree's monitor"


def test_every_monitor_channel_is_opened(states):
    channels = [c for m in states.monitors.values() for c in m.channels]
    assert len(channels) == 85 * 8 and all(OFFLINE.is_open(c) for c in channels)


def test_tree_releases_channels_when_deleted_without_close(qapp):
    states = make_states()
    w = select(states, 1020)
    channels = [c for m in states.monitors.values() for c in m.channels] + panel_channels(w)
    assert len(channels) == 85 * 8 + 2 and all(OFFLINE.is_open(c) for c in channels)
    delete_now(states)  # no closeEvent: what happens to a widget embedded in a closed screen
    del states, w
    assert not [c.address for c in channels if OFFLINE.is_open(c)]


def test_teardown_releases_channels(fresh_states):
    channels = [c for m in fresh_states.monitors.values() for c in m.channels]
    fresh_states.teardown()
    assert fresh_states.monitors == {}
    assert not [c.address for c in channels if OFFLINE.is_open(c)]


def test_standalone_panel_releases_its_own_monitor(qtbot: QtBot):
    w = EthercatTerminalStateDoubleRow()
    w.setProperty("prefix", PREFIX)
    w.setProperty("port", "7")
    channels = list(w.monitor.channels)
    assert w._owned == [w.monitor] and all(OFFLINE.is_open(c) for c in channels)
    w.setProperty("port", "8")  # re-pointing releases the previous subscription
    assert not any(OFFLINE.is_open(c) for c in channels)
    channels = list(w.monitor.channels)
    delete_now(w)
    del w
    assert not any(OFFLINE.is_open(c) for c in channels)
