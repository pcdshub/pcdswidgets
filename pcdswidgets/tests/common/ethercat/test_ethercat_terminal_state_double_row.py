"""
EthercatTerminalStateDoubleRow: the selected-terminal panel on the test data, plus standalone use.

Request tests use ``fresh_states`` (their own widget) and record the State_SP write
instead of sending it. The confirmation dialog is answered by patching QMessageBox.question.
"""

import pytest
from pytestqt.qtbot import QtBot
from qtpy import QtWidgets

from pcdswidgets.common.ethercat.ethercat_terminal_state_double_row import EthercatTerminalStateDoubleRow

from .conftest import BLUE, PREFIX, RED, feed_panel, record_writes, select, text_color, wait


def request(widget, state: str):
    """Pick a state in the Request combo box as a user would."""
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


def test_terminal_widget_fills_panel_width(states):
    states.setFixedSize(1100, 1000)  # wider than designed: the panel follows
    try:
        w = select(states, 1020)
        wait(0.3)
        panel = states.detailPanel.contentsRect().width()
        assert w.width() >= 800 and abs(w.width() - panel) <= 2, (w.width(), panel)
        assert w.height() <= 100
    finally:
        states.setFixedSize(850, 1000)


# ------------------------------------------------- requests (writes recorded)
def test_request_cancelled_writes_nothing(fresh_states, answer):
    w = select(fresh_states, 1020)
    writes = record_writes(w)
    calls = answer("no")
    request(w, "OP")
    assert len(calls) == 1 and "OP" in calls[0] and "RCC-E6" in calls[0]
    assert writes == []
    assert w.PyDMEnumComboBox_state.currentText() == "SAFEOP"  # reverted


def test_request_confirmed_writes_state_sp(fresh_states, answer):
    w = select(fresh_states, 1020)
    writes = record_writes(w)
    calls = answer("yes")
    request(w, "OP")
    assert len(calls) == 1 and f"{fresh_states.get_prefix()}ECAT:1020:State_SP" in calls[0]
    assert writes == [4]  # OP


def test_same_state_request_asks_nothing(fresh_states, answer):
    w = select(fresh_states, 1020)
    writes = record_writes(w)
    calls = answer("yes")
    request(w, "SAFEOP")
    assert calls == [] and writes == []


def test_confirmation_can_be_disabled(fresh_states, answer):
    fresh_states.setProperty("confirmRequests", False)
    w = select(fresh_states, 1020)
    assert w.property("confirmRequests") is False
    writes = record_writes(w)
    calls = answer("no")
    request(w, "PREOP")
    assert calls == [] and writes == [1]  # PREOP


def test_request_not_sent_if_locked_while_confirming(fresh_states, monkeypatch):
    """The dialog lets PV updates in: a terminal that becomes LOCKED meanwhile is not written."""
    w = select(fresh_states, 1020)
    writes = record_writes(w)
    monitor = fresh_states.monitors[1020]
    warnings = []

    def question(*_args, **_kwargs):
        monitor._on_value("disp", 1)  # DISP goes to 1 while the operator reads the dialog
        return QtWidgets.QMessageBox.Yes

    monkeypatch.setattr(QtWidgets.QMessageBox, "question", question)
    monkeypatch.setattr(QtWidgets.QMessageBox, "warning", lambda *args, **_kw: warnings.append(args[2]))
    request(w, "OP")
    assert writes == []
    assert len(warnings) == 1 and "LOCKED" in warnings[0] and "DISP" in warnings[0]
    assert w.PyDMEnumComboBox_state.currentText() == "SAFEOP"  # reverted
    assert w.accessLabel.text() == "LOCKED" and not w.requestFrame.isEnabled()


# ------------------------------------------------------------- standalone
def test_standalone_designer_defaults(qtbot: QtBot):
    w = EthercatTerminalStateDoubleRow()
    qtbot.addWidget(w)
    assert w.property("prefix") == "" and w.property("port") == ""
    assert w.property("confirmRequests") is True
    assert w.accessLabel.text() == "UNKNOWN" and not w.requestFrame.isEnabled()
    assert w.monitor is None  # nothing connects until prefix and port are set


def test_standalone_disconnected(qtbot: QtBot):
    """No IOC answers: everything reads DISCONNECTED, requests disabled. Nothing is written."""
    w = EthercatTerminalStateDoubleRow()
    qtbot.addWidget(w)
    w.setProperty("prefix", PREFIX)
    w.setProperty("port", "1015")
    w.setProperty("terminal_name", "RCC-E1")
    w.show()
    feed_panel(w)  # the plugin's "not connected" report
    assert w.PyDMLabel_rbv.channel == f"ca://{PREFIX}ECAT:1015:State_RBV"
    assert [w.PyDMLabel_rbv.text(), w.flagsLabel.text(), w.linkLabel.text()] == ["DISCONNECTED"] * 3
    assert w.accessLabel.text() == "UNKNOWN" and not w.requestFrame.isEnabled()
    assert (w.width(), w.height()) == (800, 100)
    w.disconnect_channels()


def test_standalone_monitor_uses_channel_access(qtbot: QtBot):
    w = EthercatTerminalStateDoubleRow()
    qtbot.addWidget(w)
    w.setProperty("prefix", PREFIX)
    w.setProperty("port", "1")
    assert w.PyDMLabel_rbv.channel == f"ca://{PREFIX}ECAT:1:State_RBV"
    assert w.PyDMEnumComboBox_state.channel == f"ca://{PREFIX}ECAT:1:State_SP"
    assert [c.address for c in w.monitor.channels] == [
        f"ca://{PREFIX}ECAT:1:{suffix}" for _key, suffix in type(w.monitor).FIELDS
    ]
    w.disconnect_channels()
