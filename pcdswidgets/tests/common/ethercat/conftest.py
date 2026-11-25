"""
Fixtures for the EtherCAT terminal-state widgets (``pcdswidgets.common.ethercat``).

Everything runs on MOCK data: ``mock=True`` makes the widgets use simulated
``loc://`` PVs seeded from ``data/plc-sds-raptor.json`` (a real read-only discovery
snapshot) plus ``data/plc-sds-raptor.mock.json`` (overrides: editable terminals,
non-OP states, an ERROR flag, a link fault). Nothing is read from or written to EPICS.

The only ``ca://`` tests use a prefix no IOC serves; Channel Access name searches
are kept on this host (set below, before any CA context is created).

``loc://`` channels are process-global in PyDM, so every widget fixture uses its own
PV prefix: a test that changes a simulated PV never leaks into another test.
"""

from __future__ import annotations

import itertools
import os
import time
from pathlib import Path

import pytest
from pytestqt.qtbot import QtBot
from qtpy import QtCore, QtWidgets

os.environ.setdefault("EPICS_CA_AUTO_ADDR_LIST", "NO")
os.environ.setdefault("EPICS_CA_ADDR_LIST", "127.0.0.1")

from pcdswidgets.common.ethercat.ethercat_terminal_states_stretch import (  # noqa: E402
    ROLE_PORT,
    EthercatTerminalStatesStretch,
)

DATA = Path(__file__).parent / "data"
PLC = "plc-sds-raptor"
DISCOVERY = DATA / f"{PLC}.json"
TERMINALS = 85
EDITABLE_PORTS = list(range(1014, 1022))
GREY, RED, BLUE = "#8d8d8d", "#da1e28", "#0f62fe"
_prefixes = itertools.count(1)


def find_item(tree, port: int):
    it = QtWidgets.QTreeWidgetItemIterator(tree)
    while it.value():
        if it.value().data(0, ROLE_PORT) == port:
            return it.value()
        it += 1
    return None


def top_level(tree, label_prefix: str):
    for index in range(tree.topLevelItemCount()):
        item = tree.topLevelItem(index)
        if item.text(0).startswith(label_prefix):
            return item
    return None


def ports_below(item) -> list[int]:
    ports, stack = [], [item.child(i) for i in range(item.childCount())]
    while stack:
        node = stack.pop()
        if node.data(0, ROLE_PORT) is not None:
            ports.append(node.data(0, ROLE_PORT))
        stack += [node.child(i) for i in range(node.childCount())]
    return ports


def marker_color(item, tree) -> tuple[str, int]:
    """Centre pixel of a row's status marker: (colour name, alpha)."""
    image = item.icon(0).pixmap(tree.iconSize()).toImage()
    color = image.pixelColor(image.width() // 2, image.height() // 2)
    return color.name(), color.alpha()


def text_color(widget) -> str:
    from qtpy import QtGui

    return widget.palette().color(QtGui.QPalette.WindowText).name()


def visible_ports(states: EthercatTerminalStatesStretch) -> list[int]:
    return sorted(p for p, it in states.terminal_items.items() if not it.isHidden())


def wait(seconds: float):
    """Run the Qt event loop for a while (channel callbacks, timers)."""
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.AllEvents, 50)
        time.sleep(0.01)


def wait_until(condition, timeout: float = 10.0):
    end = time.monotonic() + timeout
    while not condition():
        if time.monotonic() > end:
            raise TimeoutError(f"condition not met within {timeout} s")
        wait(0.05)


def make_states(qtbot: QtBot | None = None, mock: bool = True, prefix: str | None = None, **props):
    """A mock (or live, mock=False) EthercatTerminalStatesStretch on the test discovery file."""
    states = EthercatTerminalStatesStretch()
    if qtbot is not None:
        qtbot.addWidget(states)
    states.setProperty("mock", mock)
    states.setProperty("discoveryFile", str(DISCOVERY))
    states.setProperty("prefix", prefix or f"MOCK{next(_prefixes)}:")
    states.setProperty("plc", PLC)
    for name, value in props.items():
        states.setProperty(name, value)
    states.reload()
    states.setFixedSize(850, 1000)
    states.show()
    if mock:
        wait_until(lambda: all(m.state_text is not None for m in states.monitors.values()))
        wait(0.3)
    return states


def select(states: EthercatTerminalStatesStretch, port: int):
    """Select a terminal as a user would; return the terminal widget once it shows that port."""
    assert states.select_terminal(port), port
    widget = states.terminalWidget
    wait_until(lambda: widget.isVisible() and widget.get_macro("PORT") == str(port), timeout=5)
    if states.get_mock():
        wait_until(lambda: widget.monitor is not None and widget.monitor.value("disv") is not None, timeout=5)
    wait(0.3)
    return widget


@pytest.fixture(autouse=True)
def _no_real_ads(monkeypatch):
    """
    Never run a real ads-actions from the tests (it may be installed, e.g. on psbuild):
    only a fake one that a test sets explicitly through ADS_ACTIONS_BIN.
    """
    from pcdswidgets.common.ethercat import discover

    monkeypatch.setattr(discover, "find_ads", lambda: os.environ.get("ADS_ACTIONS_BIN") or None)


@pytest.fixture(scope="module")
def shared_states(qapp):
    """One read-only mock widget per test module (tests must not change simulated PVs)."""
    states = make_states()
    yield states
    states.teardown()
    states.close()
    states.deleteLater()


@pytest.fixture
def states(shared_states):
    """The shared mock widget, reset to: no filter, collapsed tree, nothing selected."""
    yield shared_states
    shared_states.filterEdit.setText("")
    shared_states.showCombo.setCurrentIndex(0)
    shared_states.terminalTree.setCurrentItem(None)
    shared_states.terminalTree.collapseAll()
    QtCore.QCoreApplication.processEvents()


@pytest.fixture
def fresh_states(qtbot: QtBot):
    """Private mock widget with its own loc:// PVs, for tests that change simulated PVs."""
    states = make_states(qtbot)
    yield states
    states.teardown()


@pytest.fixture
def answer(monkeypatch):
    """answer('yes' | 'no') patches the confirmation dialog and returns the list of prompts."""
    calls = []

    def set_answer(reply):
        button = QtWidgets.QMessageBox.Yes if reply == "yes" else QtWidgets.QMessageBox.No

        def question(*args, **kwargs):
            calls.append(args[2] if len(args) > 2 else "")
            return button

        monkeypatch.setattr(QtWidgets.QMessageBox, "question", question)
        return calls

    return set_answer
