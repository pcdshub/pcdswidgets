"""
EthercatTerminalStateDoubleRow: the selected-terminal panel on MOCK data, plus standalone use.

Request tests use ``fresh_states`` (own loc:// PVs) because they change the simulated
State_SP / State_RBV. The confirmation dialog is answered by patching QMessageBox.question.
"""

import pytest
from pytestqt.qtbot import QtBot

from pcdswidgets.common.ethercat.ethercat_terminal_state_double_row import EthercatTerminalStateDoubleRow

from .conftest import BLUE, RED, select, text_color, wait, wait_until


def request(widget, state: str):
    combo = widget.PyDMEnumComboBox_state
    index = combo.findText(state)
    assert index >= 0, state
    combo.setCurrentIndex(index)
    combo.activated[int].emit(index)


# ----------------------------------------------------------- read-only panel
def test_placeholder_until_selection(states):
    assert states.detailPlaceholder.isVisible()
    assert not states.terminalWidget.isVisible()


def test_editable_terminal_panel(states):
    w = select(states, 1020)  # RCC-E6: SAFEOP + ERROR flag, editable
    assert w.PyDMLabel_name.text() == "RCC-E6"
    assert w.typeLabel.text() == "EL3314"
    assert w.pvLabel.text() == f"{states.get_prefix()}ECAT:1020"
    assert w.PyDMLabel_rbv.text() == "SAFEOP"
    assert w.flagsLabel.text() == "ERROR" and text_color(w.flagsLabel) == RED
    assert w.linkLabel.text() == "OK"
    assert w.accessLabel.text() == "EDITABLE" and text_color(w.accessLabel) == BLUE
    combo = w.PyDMEnumComboBox_state
    assert w.requestFrame.isEnabled() and combo.isEnabled()
    assert [combo.itemText(i) for i in range(combo.count())] == ["INIT", "PREOP", "BOOTSTRAP", "SAFEOP", "OP"]
    assert combo.currentText() == "SAFEOP"  # shows the last request
    assert w.height() <= 100


def test_link_flags_decoded(states):
    w = select(states, 1004)  # Term 71: MULTIPLE_FLAGS
    assert w.linkLabel.text() == "ADDITIONAL_LINK \u00b7 port D"
    assert text_color(w.linkLabel) == RED


@pytest.mark.parametrize(
    "port, reasons, absent",
    [
        (1001, ["DISP", "DISA = DISV"], []),  # pytmc default deny
        (1024, ["DISA = DISV"], ["DISP:"]),
        (1028, ["DISP"], ["DISA = DISV"]),
    ],
)
def test_locked_terminal_panel(states, port, reasons, absent):
    w = select(states, port)
    tip = w.accessLabel.toolTip()
    assert w.accessLabel.text() == "LOCKED" and not w.requestFrame.isEnabled()
    assert all(r in tip for r in reasons) and not any(a in tip for a in absent)


def test_switching_terminals_reuses_panel(states):
    first = select(states, 1015)
    second = select(states, 1001)
    assert second is first  # one widget, re-pointed by its properties
    assert second.PyDMLabel_name.text() == "Term 66"
    assert second.PyDMLabel_rbv.channel.endswith("ECAT:1001:State_RBV")


@pytest.mark.parametrize("width", [850, 1100, 1536])
def test_terminal_widget_fills_panel_width(states, width):
    states.setFixedSize(width, 1000)
    try:
        w = select(states, 1020)
        wait(0.3)
        panel = states.detailPanel.contentsRect().width()
        assert w.width() >= 800 and abs(w.width() - panel) <= 2, (w.width(), panel)
        assert w.height() <= 100
    finally:
        states.setFixedSize(850, 1000)


# ----------------------------------------------------- requests (own PVs)
def test_request_cancelled_changes_nothing(fresh_states, answer):
    w = select(fresh_states, 1020)
    calls = answer("no")
    request(w, "OP")
    wait(1.5)
    assert len(calls) == 1 and "OP" in calls[0] and "RCC-E6" in calls[0]
    assert fresh_states.monitors[1020].state_text == "SAFEOP"
    assert w.PyDMEnumComboBox_state.currentText() == "SAFEOP"  # reverted


def test_request_confirmed_moves_state(fresh_states, answer):
    w = select(fresh_states, 1020)
    answer("yes")
    request(w, "OP")
    wait_until(lambda: fresh_states.monitors[1020].state_text == "OP", timeout=5)
    wait(0.5)
    assert w.PyDMLabel_rbv.text() == "OP"
    assert w.PyDMEnumComboBox_state.currentText() == "OP"
    assert w.flagsLabel.text() == "ERROR"  # flag bits kept
    fresh_states.refresh()
    assert fresh_states.terminal_items[1020].parent().text(2) == "1 NOT OP"  # only RCC-E7 left


def test_same_state_request_asks_nothing(fresh_states, answer):
    w = select(fresh_states, 1020)
    calls = answer("yes")
    request(w, "SAFEOP")
    wait(0.5)
    assert calls == []


def test_confirmation_can_be_disabled(fresh_states, answer):
    fresh_states.setProperty("confirmRequests", False)
    w = select(fresh_states, 1020)
    assert w.property("confirmRequests") is False
    calls = answer("no")
    request(w, "PREOP")
    wait_until(lambda: fresh_states.monitors[1020].state_text == "PREOP", timeout=5)
    assert calls == []


def test_absent_terminal_cannot_leave_init(fresh_states):
    """Mock rule: a NOT_PRESENT terminal stays in INIT even if a request is accepted."""
    port = next(p for p, m in fresh_states.monitors.items() if m.link_text == "NOT_PRESENT")
    fresh_states.monitors[port]._simulate_request(4)
    wait(1.2)
    assert fresh_states.monitors[port].state_text == "INIT"


# ------------------------------------------------------------- standalone
def test_standalone_designer_defaults(qtbot: QtBot):
    w = EthercatTerminalStateDoubleRow()
    qtbot.addWidget(w)
    assert w.property("prefix") == "" and w.property("port") == ""
    assert w.property("confirmRequests") is True
    assert w.accessLabel.text() == "UNKNOWN" and not w.requestFrame.isEnabled()
    assert w.monitor is None  # nothing connects until prefix and port are set


def test_standalone_live_disconnected(qtbot: QtBot):
    """ca:// with no IOC: everything reads DISCONNECTED, requests disabled. Nothing is written."""
    w = EthercatTerminalStateDoubleRow()
    qtbot.addWidget(w)
    w.setProperty("prefix", "PYTEST:NO:IOC:")
    w.setProperty("port", "1015")
    w.setProperty("terminal_name", "RCC-E1")
    w.show()
    wait(0.5)
    assert w.PyDMLabel_rbv.channel == "ca://PYTEST:NO:IOC:ECAT:1015:State_RBV"
    assert [w.PyDMLabel_rbv.text(), w.flagsLabel.text(), w.linkLabel.text()] == ["DISCONNECTED"] * 3
    assert w.accessLabel.text() == "UNKNOWN" and not w.requestFrame.isEnabled()
    assert (w.width(), w.height()) == (800, 100)
    w.disconnect_channels()


def test_protocol_switch_rewrites_every_channel(qtbot: QtBot):
    w = EthercatTerminalStateDoubleRow()
    qtbot.addWidget(w)
    w.setProperty("prefix", "PYTEST:PROTO:")
    w.setProperty("port", "1")
    w.set_channel_protocol("loc://")
    assert w.PyDMLabel_rbv.channel.startswith("loc://")
    assert w.PyDMEnumComboBox_state.channel.startswith("loc://")
    assert all(c.address.startswith("loc://PYTEST:PROTO:ECAT:1:") for c in w.monitor.channels)
    assert type(w)._widget_to_pre_template["PyDMLabel_rbv"][0][1].startswith("ca://")  # class untouched
    w.disconnect_channels()


# ------------------------------------------------- access re-checked at write
def test_request_not_sent_if_locked_while_confirming(fresh_states, monkeypatch):
    """The dialog lets PV updates in: a terminal that becomes LOCKED meanwhile is not written."""
    from qtpy import QtWidgets

    w = select(fresh_states, 1020)
    monitor = fresh_states.monitors[1020]
    warnings = []

    def question(*_args, **_kwargs):
        monitor.values["disp"] = 1  # DISP goes to 1 while the operator reads the dialog
        return QtWidgets.QMessageBox.Yes

    monkeypatch.setattr(QtWidgets.QMessageBox, "question", question)
    monkeypatch.setattr(QtWidgets.QMessageBox, "warning", lambda *args, **_kw: warnings.append(args[2]))
    sp_before = monitor.value("sp")
    request(w, "OP")
    wait(1.2)
    assert len(warnings) == 1 and "LOCKED" in warnings[0] and "DISP" in warnings[0]
    assert monitor.value("sp") == sp_before and monitor.state_text == "SAFEOP"
    assert w.PyDMEnumComboBox_state.currentText() == "SAFEOP"  # reverted
