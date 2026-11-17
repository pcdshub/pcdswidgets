"""
Shared EtherCAT terminal-state logic for the ``common.ethercat`` widgets.

Used by :class:`EthercatTerminalStateDoubleRow` (one terminal) and
:class:`EthercatTerminalStatesStretch` (every terminal of a PLC as a tree).

PVs per terminal (pytmc ``ethercat.py``), ``{prefix}ECAT:{port}:...``:

==================  =====  =====  ==============================================
PV                  Type   RO/RW  Meaning
==================  =====  =====  ==============================================
``State_RBV``       mbbi   RO     INIT / PREOP / BOOTSTRAP / SAFEOP / OP
``Link_RBV``        mbbi   RO     OK / NOT_PRESENT / ... / MULTIPLE_FLAGS
``State_SP``        mbbo   RW     requested state (same enum as ``State_RBV``)
``State_SP.DISP``   field  RO     1 = Channel Access puts disabled
``State_SP.DISA``   field  RO     record disabled when DISA == DISV
``State_SP.DISV``   field  RO
``StateRaw``        longin RO     raw state word: flags in bits 4-7 (pytmc helper)
``LinkCode``        calc   RO     link conditions bits 0-3, ports bits 4-7 (helper)
==================  =====  =====  ==============================================

A terminal is EDITABLE when ``DISP == 0`` and ``DISA != DISV`` and Channel Access
grants write access (the record semantics, as in pytmc ``effective_access()``).

Colours follow high-performance HMI practice: neutral for normal, colour only
for meaning (Carbon support-error red for faults, Blue 60 for EDITABLE).
"""

from __future__ import annotations

import functools
import json
import os
import re
from pathlib import Path

from pydm.widgets.channel import PyDMChannel
from qtpy import QtCore, QtGui
from qtpy.QtCore import Qt

MODULE_DIR = Path(__file__).resolve().parent
STATUS_QSS = MODULE_DIR / "ethercat_status.qss"
CACHE_DIR = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "ecat-states"

# Enum strings in record order (pytmc/ethercat.py). Live mode uses the strings
# reported by Channel Access; these are the fallback and the mock definition.
STATE_ENUM = ("INIT", "PREOP", "BOOTSTRAP", "SAFEOP", "OP")
LINK_ENUM = (
    "OK",
    "NOT_PRESENT",
    "LINK_WITHOUT_COMM",
    "MISSING_LINK",
    "ADDITIONAL_LINK",
    "PORT_A",
    "PORT_B",
    "PORT_C",
    "PORT_D",
    "MULTIPLE_FLAGS",
)
GOOD_STATE, GOOD_LINK = "OP", "OK"
ABSENT_LINKS = {"NOT_PRESENT", "LINK_WITHOUT_COMM", "MISSING_LINK"}
# Raw EtherCAT state word (pytmc helper records StateRaw / LinkCode):
#   bits 0-3 state code, bits 4-7 state flags, bits 8-15 link byte (conditions 0-3, ports 4-7)
STATE_CODES = {"INIT": 0x01, "PREOP": 0x02, "BOOTSTRAP": 0x03, "SAFEOP": 0x04, "OP": 0x08}
STATE_FLAG_BITS = {"ERROR": 0x10, "INVALID_VPRS": 0x20, "INITCMD_ERROR": 0x40, "DISABLED": 0x80}
LINK_FLAG_BITS = {
    "NOT_PRESENT": 0x01,
    "LINK_WITHOUT_COMM": 0x02,
    "MISSING_LINK": 0x04,
    "ADDITIONAL_LINK": 0x08,
    "PORT_A": 0x10,
    "PORT_B": 0x20,
    "PORT_C": 0x40,
    "PORT_D": 0x80,
}

# Health, ordered like EPICS severities: OK < FAULT (MAJOR) < DISCONNECTED (INVALID)
H_OK, H_FAULT, H_DISCONNECTED = 0, 1, 2
HEALTH_TEXT = {H_OK: "OK", H_FAULT: "FAULT", H_DISCONNECTED: "DISCONNECTED"}

FAULT_RED = QtGui.QColor("#da1e28")  # Carbon support-error
MUTED_GREY = QtGui.QColor("#8d8d8d")  # Carbon Gray 50: readable on light and dark themes
OK_GREY = QtGui.QColor("#8d8d8d")
LOCK_COLORS = {
    "EDITABLE": QtGui.QColor("#0f62fe"),  # Carbon Blue 60, the interaction accent
    "LOCKED": QtGui.QColor("#6f6f6f"),
    "UNKNOWN": QtGui.QColor("#c6c6c6"),
}

ACCESS_GRANTED = "State requests accepted (DISP == 0, DISA != DISV)"
TRUTHY = {"1", "true", "yes", "on"}


# ------------------------------------------------------------------ decoding
def decode_state_flags(raw) -> list[str] | None:
    """State flag names from ``StateRaw`` (bits 4-7), ``None`` if unavailable."""
    if raw is None:
        return None
    raw = int(raw)
    return [name for name, bit in STATE_FLAG_BITS.items() if raw & bit]


def decode_link_text(code) -> str | None:
    """Readable link text from ``LinkCode``, e.g. ``'ADDITIONAL_LINK · port D'``."""
    if code is None:
        return None
    code = int(code)
    conditions = [name for name, bit in LINK_FLAG_BITS.items() if bit < 0x10 and code & bit]
    ports = [name[-1] for name, bit in LINK_FLAG_BITS.items() if bit >= 0x10 and code & bit]
    if not conditions and not ports:
        return "OK"
    where = f"port{'s' if len(ports) > 1 else ''} {', '.join(ports)}" if ports else ""
    what = " + ".join(conditions)
    return f"{what} \u00b7 {where}" if what and where else (what or where)


def access_rule(disp, disa, disv, write_access=None) -> tuple[str, list[str]]:
    """
    EDITABLE / LOCKED / UNKNOWN for one terminal, with the reasons when locked.

    EDITABLE when ``DISP == 0`` and ``DISA != DISV`` and write access is not denied.
    """
    if disp is None or disa is None or disv is None:
        return "UNKNOWN", ["State_SP access fields not connected"]
    try:
        disp, disa, disv = int(disp), int(disa), int(disv)
    except (TypeError, ValueError):
        return "UNKNOWN", ["unreadable access fields"]
    reasons = []
    if disp != 0:
        reasons.append("DISP: channel-access puts disabled")
    if disa == disv:
        reasons.append("DISA = DISV: record processing disabled")
    if write_access is False:
        reasons.append("no channel-access write permission (ASG)")
    return ("LOCKED", reasons) if reasons else ("EDITABLE", [])


# -------------------------------------------------------------------- styling
def status_stylesheet() -> str:
    """The ``ecatStatus`` property rules (not a theme), applied by each widget to itself."""
    try:
        return STATUS_QSS.read_text(encoding="utf-8")
    except OSError:
        return ""


def set_status(widget, status: str):
    """Tag a label with ``ecatStatus`` (fault / editable / muted / ""); the status sheet colours it."""
    if widget.property("ecatStatus") == status:
        return
    widget.setProperty("ecatStatus", status)
    widget.style().unpolish(widget)
    widget.style().polish(widget)


def dot_pixmap(health: int, size: int) -> QtGui.QPixmap:
    """Status marker: OK = neutral grey dot, FAULT = red dot, DISCONNECTED = dashed hollow ring."""
    pixmap = QtGui.QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QtGui.QPainter(pixmap)
    painter.setRenderHint(QtGui.QPainter.Antialiasing)
    rect = QtCore.QRectF(1.5, 1.5, size - 3, size - 3)
    if health in (H_OK, H_FAULT):
        painter.setPen(Qt.NoPen)
        painter.setBrush(OK_GREY if health == H_OK else FAULT_RED)
    else:
        pen = QtGui.QPen(MUTED_GREY, 1.5)
        pen.setStyle(Qt.DashLine)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
    painter.drawEllipse(rect)
    painter.end()
    return pixmap


def lock_pixmap(access: str, size: int) -> QtGui.QPixmap:
    """Padlock: open blue = EDITABLE, closed grey = LOCKED, pale = UNKNOWN."""
    color = LOCK_COLORS.get(access, LOCK_COLORS["UNKNOWN"])
    pixmap = QtGui.QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QtGui.QPainter(pixmap)
    painter.setRenderHint(QtGui.QPainter.Antialiasing)
    painter.setPen(QtGui.QPen(color, max(1.5, size * 0.13)))
    painter.setBrush(Qt.NoBrush)
    shackle = QtCore.QRectF(size * 0.27, size * 0.06, size * 0.46, size * 0.62)
    if access == "EDITABLE":
        shackle.translate(size * 0.16, -size * 0.04)
        painter.drawArc(shackle, 0, 180 * 16)
        painter.drawLine(
            QtCore.QPointF(shackle.left(), shackle.center().y()), QtCore.QPointF(shackle.left(), size * 0.36)
        )
    else:
        painter.drawArc(shackle, 0, 180 * 16)
    painter.setPen(Qt.NoPen)
    painter.setBrush(color)
    painter.drawRoundedRect(QtCore.QRectF(size * 0.14, size * 0.42, size * 0.72, size * 0.54), size * 0.08, size * 0.08)
    painter.end()
    return pixmap


# ----------------------------------------------------------------- discovery
class Terminal:
    """One discovered terminal."""

    def __init__(
        self,
        port,
        name,
        type,
        neighbors=None,
        snapshot_state=None,
        snapshot_link=None,
        snapshot_state_flags=None,
        snapshot_link_flags=None,
    ):
        self.port = int(port)
        self.name = name
        self.type = type
        self.neighbors = dict(neighbors or {})
        self.snapshot_state = snapshot_state
        self.snapshot_link = snapshot_link
        self.snapshot_state_flags = snapshot_state_flags
        self.snapshot_link_flags = snapshot_link_flags

    @property
    def display_name(self) -> str:
        """TwinCAT name without a trailing '(<type>)' (ADS cuts names at 31 chars)."""
        match = re.match(r"^(.*?)\s*\(([^()]+)\)?$", self.name)
        if match and match.group(1) and self.type.startswith(match.group(2)):
            return match.group(1)
        return self.name


class Node:
    """Tree node: kind is "group", "branch" or "terminal"."""

    def __init__(self, kind, label, terminal=None, children=None, tooltip=""):
        self.kind = kind
        self.label = label
        self.terminal = terminal
        self.children = list(children or [])
        self.tooltip = tooltip

    def count_terminals(self) -> int:
        return (self.kind == "terminal") + sum(child.count_terminals() for child in self.children)


def load_discovery(path) -> tuple[dict, list[Terminal]]:
    """Read a discovery JSON written by :mod:`pcdswidgets.common.ethercat.discover`."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    terminals = []
    for row in data.get("terminals", []):
        snapshot = row.get("snapshot") or {}
        terminals.append(
            Terminal(
                port=int(row["port"]),
                name=str(row.get("name") or f"Port {row['port']}"),
                type=str(row.get("type") or ""),
                neighbors={k: int(v or 0) for k, v in (row.get("neighbors") or {}).items()},
                snapshot_state=snapshot.get("state"),
                snapshot_link=snapshot.get("link"),
                snapshot_state_flags=snapshot.get("state_flags"),
                snapshot_link_flags=snapshot.get("link_flags"),
            )
        )
    terminals.sort(key=lambda t: t.port)
    return data, terminals


def build_tree(terminals: list[Terminal], topology: bool) -> list[Node]:
    """
    Turn port A-D neighbours into a readable tree.

    A straight run of terminals (one downstream neighbour each) is listed flat;
    a terminal with several downstream neighbours (junction, EK1122, EP9128...)
    gets one "Port X" branch per neighbour. The first configured slave starts
    the master line; other segments with an open port A (typically Hot Connect
    groups) become their own groups.
    """
    if not terminals:
        return []
    if not topology or not any(t.neighbors for t in terminals):
        return [
            Node(
                "group",
                "Configured terminals",
                children=[Node("terminal", t.display_name, t) for t in terminals],
                tooltip="No topology available: terminals listed in configuration order",
            )
        ]
    return _TreeBuilder(terminals).groups()


class _TreeBuilder:
    """Walks the port A-D neighbour graph once (helper for :func:`build_tree`)."""

    def __init__(self, terminals: list[Terminal]):
        self.terminals = terminals
        self.by_port = {t.port: t for t in terminals}
        self.visited: set[int] = set()

    def upstream(self, t: Terminal) -> int | None:
        port = t.neighbors.get("A", 0)
        return port if port in self.by_port and port != t.port else None

    def downstream(self, t: Terminal) -> list[tuple[str, Terminal]]:
        kids = []
        for side in "BCD":
            port = t.neighbors.get(side, 0)
            if port in self.by_port and port not in self.visited and self.upstream(self.by_port[port]) == t.port:
                kids.append((side, self.by_port[port]))
        return kids

    def chain(self, start: Terminal) -> list[Node]:
        """Nodes from ``start`` downstream: flat while linear, Port branches at junctions."""
        nodes, current = [], start
        while current is not None and current.port not in self.visited:
            self.visited.add(current.port)
            node = Node("terminal", current.display_name, current)
            nodes.append(node)
            kids = self.downstream(current)
            if len(kids) == 1:
                current = kids[0][1]
                continue
            for side, kid in kids:
                node.children.append(
                    Node(
                        "branch",
                        f"Port {side}",
                        children=self.chain(kid),
                        tooltip=f"Terminals connected to EtherCAT port {side} of {current.name}",
                    )
                )
            current = None
        return nodes

    def groups(self) -> list[Node]:
        groups, standalone = [], []
        roots = [t for t in self.terminals if self.upstream(t) is None]
        for index, root in enumerate(roots):
            if root.port in self.visited:
                continue
            members = self.chain(root)
            if index == 0:
                groups.append(
                    Node("group", "Master line", children=members, tooltip="Terminals reached from the EtherCAT master")
                )
            elif len(members) == 1 and not members[0].children:
                standalone.extend(members)
            else:
                groups.append(
                    Node(
                        "group",
                        f"{root.display_name} group",
                        children=members,
                        tooltip="Segment with an open port A in the configured topology "
                        "(typically a Hot Connect group)",
                    )
                )
        if standalone:
            groups.append(
                Node(
                    "group",
                    "Standalone terminals",
                    children=standalone,
                    tooltip="Terminals without configured neighbours",
                )
            )
        leftover = [t for t in self.terminals if t.port not in self.visited]
        if leftover:
            groups.append(
                Node("group", "Unplaced terminals", children=[Node("terminal", t.display_name, t) for t in leftover])
            )
        return groups


# ---------------------------------------------------------------------- mock
def _enum_literal(strings) -> str:
    return "(" + ",".join(f"'{s}'" for s in strings) + ")"


def mock_query(key: str, seed: dict) -> str:
    """``loc://`` query string that creates a simulated PV with its initial value."""
    if key in ("state", "sp"):
        return f"?type=int&init={seed[key]}&enum_string={_enum_literal(STATE_ENUM)}"
    if key == "link":
        return f"?type=int&init={seed[key]}&enum_string={_enum_literal(LINK_ENUM)}"
    return f"?type=int&init={seed[key]}"


def mock_seeds(terminals: list[Terminal], overrides: dict | None = None) -> dict[int, dict]:
    """
    Initial values of the simulated PVs, from the discovery snapshot plus optional overrides.

    ``overrides`` (all keyed by port as a string): ``state``, ``link``, ``access``
    (``{"DISP": 0, "DISA": 0, "DISV": 1}``), ``state_flags``, ``link_flags``.
    Without overrides every terminal is locked (pytmc default DISP=DISA=DISV=1).
    """
    overrides = overrides or {}
    seeds = {}
    for t in terminals:
        port = str(t.port)
        state = overrides.get("state", {}).get(port) or t.snapshot_state or "OP"
        link = overrides.get("link", {}).get(port) or t.snapshot_link or "OK"
        state_index = STATE_ENUM.index(state) if state in STATE_ENUM else 0
        gates = {"DISP": 1, "DISA": 1, "DISV": 1}
        gates.update(overrides.get("access", {}).get(port, {}))
        link_flags = overrides.get("link_flags", {}).get(port, t.snapshot_link_flags)
        if link_flags is None:  # old snapshot: single-flag enums only
            link_flags = [] if link == "OK" else [link] if link in LINK_FLAG_BITS else []
        state_flags = overrides.get("state_flags", {}).get(port, t.snapshot_state_flags or [])
        link_code = sum(LINK_FLAG_BITS.get(f, 0) for f in link_flags)
        raw = (link_code << 8) | sum(STATE_FLAG_BITS.get(f, 0) for f in state_flags) | STATE_CODES.get(state, 0x01)
        seeds[t.port] = {
            "state": state_index,
            "link": LINK_ENUM.index(link) if link in LINK_ENUM else 1,
            "sp": state_index,
            "disp": int(gates["DISP"]),
            "disa": int(gates["DISA"]),
            "disv": int(gates["DISV"]),
            "raw": raw,
            "linkcode": link_code,
        }
    return seeds


def mock_resend(prefix: str, port: int):
    """
    Mock only: re-broadcast the simulated PVs of one terminal to newly created widgets.

    PyDM's ``loc://`` plugin sends enum strings to the first listener only, and
    hands a new listener its value before its connection state. Channel Access
    has neither problem.
    """
    from pydm.data_plugins import plugin_for_address

    plugin = plugin_for_address("loc://mock-resend")
    for _key, suffix in TerminalMonitor.FIELDS:
        connection = plugin.connections.get(f"{prefix}ECAT:{port}:{suffix}")
        if connection is None:
            continue
        strings = getattr(connection, "_enum_string", None)
        if strings:
            connection.enum_strings_signal.emit(tuple(strings))
        if getattr(connection, "value", None) is not None:
            connection.send_new_value(connection.value)


# ------------------------------------------------------------------- monitor
class TerminalMonitor(QtCore.QObject):
    """Read-only subscription to one terminal's PVs (plus the mock simulation)."""

    changed = QtCore.Signal()
    simulated_rbv = QtCore.Signal(int)  # mock only: drives the simulated State_RBV
    simulated_raw = QtCore.Signal(int)  # mock only: drives the simulated StateRaw

    FIELDS = (
        ("state", "State_RBV"),
        ("link", "Link_RBV"),
        ("sp", "State_SP"),
        ("disp", "State_SP.DISP"),
        ("disa", "State_SP.DISA"),
        ("disv", "State_SP.DISV"),
        ("raw", "StateRaw"),  # pytmc helper records
        ("linkcode", "LinkCode"),
    )

    def __init__(self, terminal: Terminal, prefix: str, protocol: str, mock_seed: dict | None = None, parent=None):
        super().__init__(parent)
        self.terminal = terminal
        self.base = f"{prefix}ECAT:{terminal.port}"
        self.mock_seed = mock_seed
        self.values = {key: None for key, _ in self.FIELDS}
        self.connected = {key: False for key, _ in self.FIELDS}
        self.enums: dict[str, tuple] = {}
        self.write_access = None
        self._last_sp = None
        self.channels = []
        for key, suffix in self.FIELDS:
            address = f"{protocol}{self.base}:{suffix}"
            if mock_seed is not None:
                address += mock_query(key, mock_seed)
            self.channels.append(
                PyDMChannel(
                    address=address,
                    connection_slot=functools.partial(self._on_connection, key),
                    value_slot=functools.partial(self._on_value, key),
                    enum_strings_slot=(
                        functools.partial(self._on_enums, key) if key in ("state", "link", "sp") else None
                    ),
                    write_access_slot=self._on_write_access if key == "sp" else None,
                    value_signal=(
                        {"state": self.simulated_rbv, "raw": self.simulated_raw}.get(key) if mock_seed else None
                    ),
                )
            )

    def connect_channels(self):
        for channel in self.channels:
            channel.connect()

    def disconnect_channels(self):
        while self.channels:
            channel = self.channels.pop()
            try:
                channel.disconnect()
            except Exception:
                pass

    # slots
    def _on_connection(self, key, connected):
        if self.mock_seed is not None and not connected:
            return  # PyDM loc:// quirk: the first listener gets a stray False after True
        self.connected[key] = bool(connected)
        self.changed.emit()

    def _on_value(self, key, value):
        self.values[key] = value
        if self.mock_seed is not None:
            self.connected[key] = True
        if key == "sp" and self.mock_seed is not None:
            if self._last_sp is not None and value != self._last_sp:
                self._simulate_request(value)
            self._last_sp = value
        self.changed.emit()

    def _on_enums(self, key, strings):
        self.enums[key] = tuple(strings or ())
        self.changed.emit()

    def _on_write_access(self, allowed):
        self.write_access = bool(allowed)
        self.changed.emit()

    def _simulate_request(self, value):
        """Mock: a present terminal follows the request after a short delay."""
        if self.link_text in ABSENT_LINKS:
            return  # an absent terminal cannot leave INIT
        try:
            target = int(value)
        except (TypeError, ValueError):
            return
        raw = self.values.get("raw")
        new_raw = None
        if raw is not None and 0 <= target < len(STATE_ENUM):
            new_raw = (int(raw) & ~0x0F) | STATE_CODES[STATE_ENUM[target]]

        def apply():
            self.simulated_rbv.emit(target)
            if new_raw is not None:
                self.simulated_raw.emit(new_raw)

        QtCore.QTimer.singleShot(800, apply)

    # derived status
    def _enum_text(self, key, fallback):
        if not self.connected[key] or self.values[key] is None:
            return None
        value = self.values[key]
        if isinstance(value, str):
            return value
        strings = self.enums.get(key) or fallback
        try:
            index = int(value)
        except (TypeError, ValueError):
            return "UNKNOWN"
        return strings[index] if 0 <= index < len(strings) else "UNKNOWN"

    def _value(self, key):
        return self.values.get(key) if self.connected.get(key) else None

    @property
    def state_text(self):
        return self._enum_text("state", STATE_ENUM)

    @property
    def link_text(self):
        return self._enum_text("link", LINK_ENUM)

    @property
    def state_flags(self) -> list[str] | None:
        return decode_state_flags(self._value("raw"))

    @property
    def link_detail(self) -> str | None:
        return decode_link_text(self._value("linkcode"))

    @property
    def health(self) -> int:
        state, link = self.state_text, self.link_text
        if state is None or link is None:
            return H_DISCONNECTED
        if self.state_flags:
            return H_FAULT  # e.g. OP with the ERROR flag set
        return H_OK if (state == GOOD_STATE and link == GOOD_LINK) else H_FAULT

    @property
    def access(self) -> tuple[str, list[str]]:
        return access_rule(self._value("disp"), self._value("disa"), self._value("disv"), self.write_access)
