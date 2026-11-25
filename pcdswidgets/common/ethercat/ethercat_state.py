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
import re
from pathlib import Path

from pydm.data_plugins import is_read_only
from pydm.widgets.channel import PyDMChannel
from qtpy import QtCore, QtGui
from qtpy.QtCore import Qt

from pcdswidgets.common.ethercat.constants import LINK_ENUM, STATE_ENUM

STATUS_QSS = Path(__file__).resolve().parent / "ethercat_status.qss"

GOOD_STATE, GOOD_LINK = "OP", "OK"
# Raw EtherCAT state word (pytmc helper records StateRaw / LinkCode):
#   bits 0-3 state code, bits 4-7 state flags, bits 8-15 link byte (conditions 0-3, ports 4-7)
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
HEALTHS = (H_OK, H_FAULT, H_DISCONNECTED)

FAULT_RED = QtGui.QColor("#da1e28")  # Carbon support-error
MUTED_GREY = QtGui.QColor("#8d8d8d")  # Carbon Gray 50: OK markers and muted text, light and dark themes
LOCK_COLORS = {
    "EDITABLE": QtGui.QColor("#0f62fe"),  # Carbon Blue 60, the interaction accent
    "LOCKED": QtGui.QColor("#6f6f6f"),
    "UNKNOWN": QtGui.QColor("#c6c6c6"),
}

ACCESS_GRANTED = "State requests accepted (DISP == 0, DISA != DISV)"
READ_ONLY_NOTE = (
    "This PyDM session is read-only (Qt Designer or pydm --read-only): Channel Access write "
    "permission is not checked and state requests are disabled here."
)


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


def session_read_only() -> bool:
    """True in a read-only PyDM session: Qt Designer, or ``pydm --read-only``."""
    return bool(is_read_only())


def access_rule(disp, disa, disv, write_access=None) -> tuple[str, list[str]]:
    """
    EDITABLE / LOCKED / UNKNOWN for one terminal, with the reasons when locked.

    EDITABLE when ``DISP == 0`` and ``DISA != DISV`` and write access is not denied.
    In a read-only PyDM session (Qt Designer, ``pydm --read-only``) every channel
    reports no write access regardless of the IOC, so write access is ignored there:
    the answer then comes from the record fields only.
    """
    if session_read_only():
        write_access = None
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


def access_tooltip(access: str, reasons: list[str]) -> str:
    """Tooltip for an access value: the lock reasons, plus a note in read-only PyDM sessions."""
    text = f"{access}\n" + ("\n".join(reasons) if reasons else ACCESS_GRANTED)
    if session_read_only():
        text += f"\n\n{READ_ONLY_NOTE}"
    return text


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


def _icon_painter(size: int) -> tuple[QtGui.QPixmap, QtGui.QPainter]:
    """A transparent ``size`` x ``size`` pixmap and an antialiased painter on it (call ``end()``)."""
    pixmap = QtGui.QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QtGui.QPainter(pixmap)
    painter.setRenderHint(QtGui.QPainter.Antialiasing)
    return pixmap, painter


def dot_pixmap(health: int, size: int) -> QtGui.QPixmap:
    """Status marker: OK = neutral grey dot, FAULT = red dot, DISCONNECTED = dashed hollow ring."""
    pixmap, painter = _icon_painter(size)
    rect = QtCore.QRectF(1.5, 1.5, size - 3, size - 3)
    if health in (H_OK, H_FAULT):
        painter.setPen(Qt.NoPen)
        painter.setBrush(MUTED_GREY if health == H_OK else FAULT_RED)
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
    pixmap, painter = _icon_painter(size)
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

    def __init__(self, port, name, type, neighbors=None):
        self.port = int(port)
        self.name = name
        self.type = type
        self.neighbors = dict(neighbors or {})

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
        terminals.append(
            Terminal(
                port=int(row["port"]),
                name=str(row.get("name") or f"Port {row['port']}"),
                type=str(row.get("type") or ""),
                neighbors={k: int(v or 0) for k, v in (row.get("neighbors") or {}).items()},
            )
        )
    terminals.sort(key=lambda t: t.port)
    return data, terminals


def build_tree(terminals: list[Terminal]) -> list[Node]:
    """
    Turn port A-D neighbours into a readable tree.

    A straight run of terminals (one downstream neighbour each) is listed flat;
    a terminal with several downstream neighbours (junction, EK1122, EP9128...)
    gets one "Port X" branch per neighbour. The first configured slave starts
    the master line; other segments with an open port A (typically Hot Connect
    groups) become their own groups. Without any neighbour the list stays flat.
    """
    if not terminals:
        return []
    if not any(any(t.neighbors.values()) for t in terminals):
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


# ------------------------------------------------------------------- monitor
def release_monitors(monitors: list | dict):
    """
    Disconnect every monitor in a list or dict (which is emptied, so later calls are no-ops).

    Widgets connect this to their ``destroyed`` signal with :func:`functools.partial`
    on the container: Qt does not drop PyDM channel slots by itself, so without it a
    deleted widget leaves its Channel Access connections open.
    """
    while monitors:
        monitor = monitors.popitem()[1] if isinstance(monitors, dict) else monitors.pop()
        monitor.disconnect_channels()


class TerminalMonitor(QtCore.QObject):
    """
    Read-only Channel Access subscription to one terminal's PVs, with the derived
    state / link / access. Shared by both widgets.
    """

    changed = QtCore.Signal()

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

    def __init__(self, terminal: Terminal, prefix: str, parent=None):
        super().__init__(parent)
        self.terminal = terminal
        self.base = f"{prefix}ECAT:{terminal.port}"
        self.values = {key: None for key, _ in self.FIELDS}
        self.connected = {key: False for key, _ in self.FIELDS}
        self.enums: dict[str, tuple] = {}
        self.write_access = None
        self.channels = []
        for key, suffix in self.FIELDS:
            self.channels.append(
                PyDMChannel(
                    address=f"ca://{self.base}:{suffix}",
                    connection_slot=functools.partial(self._on_connection, key),
                    value_slot=functools.partial(self._on_value, key),
                    enum_strings_slot=(
                        functools.partial(self._on_enums, key) if key in ("state", "link", "sp") else None
                    ),
                    write_access_slot=self._on_write_access if key == "sp" else None,
                )
            )

    def connect_channels(self):
        for channel in self.channels:
            channel.connect()

    def disconnect_channels(self):
        """Disconnect and drop every channel (the list is emptied, so later calls are no-ops)."""
        while self.channels:
            channel = self.channels.pop()
            try:
                channel.disconnect()
            except Exception:
                pass

    # slots
    def _on_connection(self, key, connected):
        self.connected[key] = bool(connected)
        self.changed.emit()

    def _on_value(self, key, value):
        self.values[key] = value
        self.changed.emit()

    def _on_enums(self, key, strings):
        self.enums[key] = tuple(strings or ())
        self.changed.emit()

    def _on_write_access(self, allowed):
        self.write_access = bool(allowed)
        self.changed.emit()

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

    def value(self, key):
        """Last value of one field (a key of :attr:`FIELDS`), ``None`` while disconnected."""
        return self.values.get(key) if self.connected.get(key) else None

    @property
    def state_text(self):
        return self._enum_text("state", STATE_ENUM)

    @property
    def link_text(self):
        return self._enum_text("link", LINK_ENUM)

    @property
    def state_flags(self) -> list[str] | None:
        return decode_state_flags(self.value("raw"))

    @property
    def link_detail(self) -> str | None:
        return decode_link_text(self.value("linkcode"))

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
        return access_rule(self.value("disp"), self.value("disa"), self.value("disv"), self.write_access)
