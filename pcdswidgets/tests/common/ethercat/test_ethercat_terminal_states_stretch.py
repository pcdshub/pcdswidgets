"""EthercatTerminalStatesStretch on the test data set (read-only: no value is changed here)."""

import pytest
from qtpy import QtCore, QtWidgets

from .conftest import (
    EDITABLE_PORTS,
    GREY,
    RED,
    TERMINALS,
    marker_color,
    ports_below,
    top_level,
    visible_ports,
    wait,
)


def test_loads_all_terminals(states):
    assert len(states.monitors) == TERMINALS
    assert all(m.state_text is not None for m in states.monitors.values()), "every monitor has data"
    assert states.DeviceName.text() == "EtherCAT Terminal States - plc-sds-raptor"


def test_states_use_enum_strings(states):
    texts = [m.state_text for m in states.monitors.values()]
    assert not [s for s in texts if s.isdigit()]
    assert texts.count("OP") == 27 and texts.count("INIT") == 56
    assert {"SAFEOP", "PREOP"} <= set(texts)


def test_tree_collapsed_with_master_line_first(states):
    tree = states.terminalTree
    tops = [tree.topLevelItem(i) for i in range(tree.topLevelItemCount())]
    assert tops[0].text(0) == "Master line (29)"
    assert not any(t.isExpanded() for t in tops)


@pytest.mark.parametrize(
    "group, state, link",
    [
        ("Master line", "2 NOT OP", "1 NOT OK"),
        ("ALI group", "9 NOT OP", "9 NOT OK"),
        ("Standalone terminals", "4 NOT OP", "4 NOT OK"),
    ],
)
def test_group_rollup_text(states, group, state, link):
    item = top_level(states.terminalTree, group)
    assert (item.text(2), item.text(3)) == (state, link)


def test_every_group_dot_is_worst_status_below(states):
    tree, want = states.terminalTree, {0: GREY, 1: RED}
    checked, it = 0, QtWidgets.QTreeWidgetItemIterator(tree)
    while it.value():
        item = it.value()
        if item.data(0, QtCore.Qt.UserRole + 1) is None and item.childCount():
            worst = max(states.monitors[p].health for p in ports_below(item))
            assert marker_color(item, tree)[0] == want[worst], item.text(0)
            checked += 1
        it += 1
    assert checked >= 15


def test_every_terminal_dot_is_worst_of_itself_and_below(states):
    tree, want = states.terminalTree, {0: GREY, 1: RED}
    for port, row in states.terminal_items.items():
        worst = max(states.monitors[q].health for q in ports_below(row) + [port])
        assert marker_color(row, tree)[0] == want[worst], row.text(0)


def test_junction_terminal_rolls_up_downstream(states):
    """Box 93 / FEL-SIM are OP themselves; RCC-E6/E7 below them are faulty."""
    tree = states.terminalTree
    for port in (1012, 1013):
        row = states.terminal_items[port]
        assert (row.text(2), row.text(3)) == ("OP", "OK")
        assert marker_color(row, tree)[0] == RED, row.text(0)
        assert "not OK (dot shows the worst status below)" in row.toolTip(0)


def test_ok_rows_neutral_fault_rows_red(states):
    assert states.terminal_items[1001].data(2, QtCore.Qt.ForegroundRole) is None
    assert states.terminal_items[1021].data(2, QtCore.Qt.ForegroundRole).color().name() == RED


def test_access_column(states):
    editable = sorted(p for p, m in states.monitors.items() if m.access[0] == "EDITABLE")
    assert editable == EDITABLE_PORTS
    tip = states.terminal_items[1001].toolTip(4)
    assert tip.startswith("LOCKED") and "DISP" in tip and "DISA = DISV" in tip
    assert states.monitors[1024].access == ("LOCKED", ["DISA = DISV: record processing disabled"])
    assert states.monitors[1028].access == ("LOCKED", ["DISP: channel-access puts disabled"])


def test_link_tooltip_decodes_flags(states):
    assert states.monitors[1004].link_text == "MULTIPLE_FLAGS"
    assert "ADDITIONAL_LINK \u00b7 port D" in states.terminal_items[1004].toolTip(3)


@pytest.mark.parametrize(
    "mode, expected",
    [
        (1, lambda m: m.health != 0),  # Faults
        (2, lambda m: m.state_text != "OP"),  # Not OP
        (3, lambda m: m.link_text != "OK"),  # Link not OK
        (4, lambda m: m.access[0] == "EDITABLE"),  # Editable
    ],
)
def test_show_filter(states, mode, expected):
    states.showCombo.setCurrentIndex(mode)
    wait(0.2)
    matches = {p for p, m in states.monitors.items() if expected(m)}
    visible = set(visible_ports(states))
    assert matches and matches <= visible
    for port in visible - matches:  # anything else is only context: a parent of a match
        assert set(ports_below(states.terminal_items[port])) & matches


def test_editable_filter_context(states):
    states.showCombo.setCurrentIndex(4)
    wait(0.2)
    assert sorted(set(visible_ports(states)) - set(EDITABLE_PORTS)) == [1012, 1013]


def test_text_filter_and_clear(states):
    states.filterEdit.setText("pcm")
    wait(0.2)
    matching = [p for p in visible_ports(states) if "pcm" in states.monitors[p].terminal.name.lower()]
    assert len(matching) == 18
    states.filterEdit.setText("")
    wait(0.2)
    assert len(visible_ports(states)) == TERMINALS
