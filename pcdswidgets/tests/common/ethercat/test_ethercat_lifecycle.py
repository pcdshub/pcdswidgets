"""
Connection lifecycle of the EtherCAT widgets: PV subscriptions are shared, not duplicated,
and released when a widget is deleted (also without a closeEvent, e.g. embedded in a screen).
"""

from pydm.data_plugins import plugin_for_address
from pytestqt.qtbot import QtBot
from qtpy import QtCore

from pcdswidgets.common.ethercat.ethercat_terminal_state_double_row import EthercatTerminalStateDoubleRow

from .conftest import make_states, select, wait


def listeners(address: str) -> int:
    """Listeners of a loc:// connection (0 once it is closed)."""
    connection = plugin_for_address("loc://x").connections.get(address)
    return connection.listener_count if connection is not None else 0


def delete_now(widget):
    """deleteLater() and run the deferred delete (processEvents() alone does not)."""
    widget.deleteLater()
    QtCore.QCoreApplication.sendPostedEvents(None, QtCore.QEvent.DeferredDelete)
    wait(0.2)


def test_panel_shares_the_tree_monitor(states):
    w = select(states, 1020)
    assert w.monitor is states.monitors[1020]  # no second subscription for the selection
    assert w._owned == []
    select(states, 1001)
    assert w.monitor is states.monitors[1001]
    assert states.monitors[1020].channels, "switching terminals must not disconnect the tree's monitor"


def test_tree_releases_channels_when_deleted_without_close(qapp):
    states = make_states(prefix="LIFECYCLE:")
    select(states, 1020)
    address = "LIFECYCLE:ECAT:1001:State_RBV"
    assert listeners(address) == 1
    delete_now(states)  # no closeEvent: what happens to a widget embedded in a closed screen
    del states
    assert listeners(address) == 0
    assert listeners("LIFECYCLE:ECAT:1020:State_SP.DISP") == 0


def test_standalone_panel_releases_its_own_monitor(qtbot: QtBot):
    w = EthercatTerminalStateDoubleRow()
    w.setProperty("prefix", "LIFECYCLE:SOLO:")
    w.setProperty("port", "7")
    w.set_channel_protocol("loc://")
    address = "LIFECYCLE:SOLO:ECAT:7:StateRaw"
    assert w._owned == [w.monitor] and listeners(address) == 1
    delete_now(w)
    del w
    assert listeners(address) == 0


def test_rediscover_button_is_never_an_auto_run(states, monkeypatch):
    calls = []
    monkeypatch.setattr(type(states), "rediscover", lambda self, auto=False: calls.append(auto))
    states.rediscoverButton.setEnabled(True)
    states.rediscoverButton.click()
    assert calls == [False]
