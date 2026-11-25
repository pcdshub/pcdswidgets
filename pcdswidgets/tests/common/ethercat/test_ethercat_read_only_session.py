"""
Read-only PyDM sessions (Qt Designer, ``pydm --read-only``): pydm reports *no write
access* for every channel there, whatever the IOC's access security says. That must
not turn editable terminals into LOCKED ones; requests stay disabled with a note.
"""

import pytest
from pydm.data_plugins import is_read_only, set_read_only

from pcdswidgets.common.ethercat.model import access_rule
from pcdswidgets.common.ethercat.monitor import session_read_only

from .conftest import EDITABLE_PORTS, make_states, select


@pytest.fixture
def read_only_session():
    """What pydm's designer plugin does (pydm/qtdesigner.py: set_read_only(True))."""
    previous = is_read_only()
    set_read_only(True)
    yield
    set_read_only(previous)


def test_session_is_detected(read_only_session):
    assert session_read_only()


def test_rule_ignores_write_access_only_in_read_only_sessions():
    assert access_rule(0, 0, 1, write_access=False, read_only=True) == ("EDITABLE", [])
    assert access_rule(1, 1, 1, write_access=False, read_only=True)[0] == "LOCKED"  # record fields still lock
    assert access_rule(0, 0, 1, write_access=False)[0] == "LOCKED"  # normal session: ASG honoured


def test_tree_keeps_editable_terminals_in_read_only_session(qtbot, read_only_session):
    states = make_states(qtbot)
    try:
        for monitor in states.monitors.values():  # what Channel Access reports in a read-only session
            monitor.write_access = False
        states.repaint_status()
        editable = sorted(p for p, m in states.monitors.items() if m.access[0] == "EDITABLE")
        assert editable == EDITABLE_PORTS
        tip = states.terminal_items[1020].toolTip(4)
        assert tip.startswith("EDITABLE") and "read-only" in tip
    finally:
        states.teardown()


def test_panel_shows_editable_but_disables_requests_in_read_only_session(qtbot, read_only_session):
    states = make_states(qtbot)
    try:
        w = select(states, 1020)
        w.monitor.write_access = False  # what Channel Access reports in a read-only session
        w._repaint_status()
        assert w.accessLabel.text() == "EDITABLE"
        assert not w.requestFrame.isEnabled()
        assert "read-only" in w.accessLabel.toolTip() and "read-only" in w.requestFrame.toolTip()
        locked = select(states, 1001)
        assert locked.accessLabel.text() == "LOCKED"
    finally:
        states.teardown()
