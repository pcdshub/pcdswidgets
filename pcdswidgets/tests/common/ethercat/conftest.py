"""
Fixtures for the EtherCAT terminal-state widgets (``pcdswidgets.common.ethercat``).

Every test is OFFLINE. :class:`OfflineChannels` replaces ``PyDMChannel.connect`` /
``disconnect`` for this test package: no data plugin, no Channel Access, no network.
It only records which channels are open, so lifecycle tests can check that widgets
release them. A channel that never hears anything is "not connected", exactly like an
unreachable IOC. :data:`PREFIX` is therefore just a string.

Values are delivered by the tests themselves: :func:`feed` calls each
:class:`TerminalMonitor`'s channel slots (the entry points Channel Access uses) with
the states recorded on the live PLC (``data/plc-sds-raptor.states.json``) plus
:data:`OVERRIDES` (editable terminals, non-OP states, an ERROR flag, a link fault).
The tree comes from ``data/plc-sds-raptor.json``, a real read-only discovery file.
The panel's PyDM widgets are fed the same way (:func:`feed_panel`), and State_SP
writes are recorded, never sent (:func:`record_writes`).
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import pytest
from pydm import data_plugins
from pydm.widgets.channel import PyDMChannel
from pytestqt.qtbot import QtBot
from qtpy import QtCore, QtWidgets

from pcdswidgets.common.ethercat.constants import LINK_ENUM, STATE_ENUM
from pcdswidgets.common.ethercat.ethercat_state import LINK_FLAG_BITS, STATE_FLAG_BITS, TerminalMonitor
from pcdswidgets.common.ethercat.ethercat_terminal_states_stretch import ROLE_PORT, EthercatTerminalStatesStretch

DATA = Path(__file__).parent / "data"
PLC = "plc-sds-raptor"
DISCOVERY = DATA / f"{PLC}.json"
RECORDED_STATES = DATA / f"{PLC}.states.json"  # state / link / flags seen on the live PLC
TERMINALS = 85
EDITABLE_PORTS = list(range(1014, 1022))
PREFIX = "TEST:IOC:"  # any string: nothing is ever connected
GREY, RED, BLUE = "#8d8d8d", "#da1e28", "#0f62fe"


# ------------------------------------------------------------------- offline
class OfflineChannels:
    """Stands in for every PyDM data plugin: records connected channels, never opens one."""

    def __init__(self):
        self.open: list[PyDMChannel] = []

    def connect(self, channel: PyDMChannel):
        if channel.address and not self.is_open(channel):
            self.open.append(channel)

    def disconnect(self, channel: PyDMChannel):
        self.open = [c for c in self.open if c is not channel]

    def is_open(self, channel: PyDMChannel) -> bool:
        return any(c is channel for c in self.open)


OFFLINE = OfflineChannels()


def _plugin_connections() -> set[tuple[str, str]]:
    return {(name, address) for name, plugin in data_plugins.plugin_modules.items() for address in plugin.connections}


@pytest.fixture(scope="package", autouse=True)
def offline_channels():
    """
    No test in this package ever reaches a data plugin. Package scope: applied before any
    widget of this package is built, and undone before the rest of the repository's tests.
    """
    before = _plugin_connections()
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(PyDMChannel, "connect", lambda self: OFFLINE.connect(self))
        patch.setattr(PyDMChannel, "disconnect", lambda self, destroying=False: OFFLINE.disconnect(self))
        yield OFFLINE
    reached = _plugin_connections() - before
    assert not reached, f"a test reached a real data plugin: {sorted(reached)}"


# ------------------------------------------------------------------ test data
UNLOCKED = {"DISP": 0, "DISA": 0, "DISV": 1}
# Applied on top of the recorded states. Access follows pytmc: EDITABLE when DISP == 0
# and DISA != DISV; the default is DISP=DISA=DISV=1 (locked). 1004 reproduces a link
# condition seen on the live PLC (ADDITIONAL_LINK on port D, Link_RBV MULTIPLE_FLAGS).
OVERRIDES = {
    "state": {1020: "SAFEOP", 1021: "PREOP"},
    "access": {
        **dict.fromkeys(EDITABLE_PORTS, UNLOCKED),
        1024: {"DISP": 0, "DISA": 1, "DISV": 1},  # locked by DISA == DISV only
        1025: {"DISP": 0, "DISA": 1, "DISV": 1},
        1028: {"DISP": 1, "DISA": 0, "DISV": 1},  # locked by DISP only
    },
    "state_flags": {1020: ["ERROR"]},
    "link": {1004: "MULTIPLE_FLAGS"},
    "link_flags": {1004: ["ADDITIONAL_LINK", "PORT_D"]},
}
STATE_CODES = {"INIT": 0x01, "PREOP": 0x02, "BOOTSTRAP": 0x03, "SAFEOP": 0x04, "OP": 0x08}


def seed_values(overrides: dict = OVERRIDES) -> dict[int, dict]:
    """PV values per port (keys of ``TerminalMonitor.FIELDS``): recorded states plus overrides."""
    seeds = {}
    for port_text, snap in json.loads(RECORDED_STATES.read_text()).items():
        port = int(port_text)
        state = overrides["state"].get(port) or snap.get("state") or "OP"
        link = overrides["link"].get(port) or snap.get("link") or "OK"
        gates = {"DISP": 1, "DISA": 1, "DISV": 1, **overrides["access"].get(port, {})}
        link_flags = overrides["link_flags"].get(port, snap.get("link_flags") or [])
        state_flags = overrides["state_flags"].get(port, snap.get("state_flags") or [])
        link_code = sum(LINK_FLAG_BITS.get(f, 0) for f in link_flags)
        flag_bits = sum(STATE_FLAG_BITS.get(f, 0) for f in state_flags)
        seeds[port] = {
            "state": STATE_ENUM.index(state),
            "link": LINK_ENUM.index(link),
            "sp": STATE_ENUM.index(state),
            "disp": gates["DISP"],
            "disa": gates["DISA"],
            "disv": gates["DISV"],
            "raw": (link_code << 8) | flag_bits | STATE_CODES[state],
            "linkcode": link_code,
        }
    return seeds


def feed(monitor: TerminalMonitor, values: dict, write_access: bool = True):
    """Deliver PV values to a monitor through its channel slots, as Channel Access would."""
    for key, _suffix in TerminalMonitor.FIELDS:
        monitor._on_connection(key, True)
    for key, strings in (("state", STATE_ENUM), ("link", LINK_ENUM), ("sp", STATE_ENUM)):
        monitor._on_enums(key, strings)
    for key, value in values.items():
        monitor._on_value(key, value)
    monitor._on_write_access(write_access)


def feed_panel(widget):
    """
    Give the panel's PyDM widgets (State_RBV label, State_SP combo) the monitor's values,
    or the "not connected" report a plugin sends for an unreachable IOC if it has none.
    """
    monitor = widget.monitor
    pydm_widgets = ((widget.PyDMLabel_rbv, "state"), (widget.PyDMEnumComboBox_state, "sp"))
    if monitor is None or monitor.state_text is None:
        for pydm_widget, _key in pydm_widgets:
            pydm_widget.connection_changed(False)
        return
    for pydm_widget, key in pydm_widgets:
        pydm_widget.connection_changed(True)
        pydm_widget.enum_strings_changed(STATE_ENUM)
        pydm_widget.value_changed(monitor.values[key])
    widget.PyDMEnumComboBox_state.write_access_changed(True)


def record_writes(widget, monkeypatch) -> list[int]:
    """Record a panel's State_SP writes (enum indexes) instead of sending them."""
    writes = []
    monkeypatch.setattr(widget.PyDMEnumComboBox_state, "internal_combo_box_activated_int", writes.append)
    return writes


# -------------------------------------------------------------- tree helpers
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


# ------------------------------------------------------------------ widgets
def make_states(qtbot: QtBot | None = None, fed: bool = True, **props):
    """
    An EthercatTerminalStatesStretch on the test discovery file (offline).

    ``fed``: every monitor gets the values of :func:`seed_values`; otherwise every
    terminal stays "not connected", as with an unreachable IOC.
    """
    states = EthercatTerminalStatesStretch()
    if qtbot is not None:
        qtbot.addWidget(states)
    states.setProperty("discoveryFile", str(DISCOVERY))
    states.setProperty("prefix", PREFIX)
    states.setProperty("plc", PLC)
    for name, value in props.items():
        states.setProperty(name, value)
    states.reload()
    states.setFixedSize(850, 1000)
    states.show()
    if fed:
        seeds = seed_values()
        for port, monitor in states.monitors.items():
            feed(monitor, seeds[port])
        states.refresh()
    return states


def select(states: EthercatTerminalStatesStretch, port: int):
    """Select a terminal as a user would; return the panel, its PyDM widgets fed (see feed_panel)."""
    assert states.select_terminal(port), port
    widget = states.terminalWidget
    assert widget.isVisible() and widget.get_macro("PORT") == str(port)
    feed_panel(widget)
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
    """One widget per test module (tests must not change its values)."""
    states = make_states()
    yield states
    states.teardown()
    states.close()
    states.deleteLater()


@pytest.fixture
def states(shared_states):
    """The shared widget, reset to: no filter, collapsed tree, nothing selected."""
    yield shared_states
    shared_states.filterEdit.setText("")
    shared_states.showCombo.setCurrentIndex(0)
    shared_states.terminalTree.setCurrentItem(None)
    shared_states.terminalTree.collapseAll()
    QtCore.QCoreApplication.processEvents()


@pytest.fixture
def fresh_states(qtbot: QtBot):
    """Private widget, for tests that change its values."""
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
