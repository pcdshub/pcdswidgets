"""
Qt-free model of the ``common.ethercat`` widgets: decoding, rules, tree and roll-ups.

PVs per terminal (pytmc ``ethercat.py``), ``{prefix}ECAT:{port}:...``:

==================  ======  =====  ==============================================
PV                  Type    RO/RW  Meaning
==================  ======  =====  ==============================================
``State_RBV``       mbbi    RO     INIT / PREOP / BOOTSTRAP / SAFEOP / OP
``Link_RBV``        mbbi    RO     OK / NOT_PRESENT / ... / MULTIPLE_FLAGS
``State_SP``        mbbo    RW     requested state (same enum as ``State_RBV``)
``State_SP.DISP``   field   RO     1 = Channel Access puts disabled
``State_SP.DISA``   field   RO     record disabled when DISA == DISV
``State_SP.DISV``   field   RO
``StateRaw``        longin  RO     raw state word: flags in bits 4-7 (pytmc helper)
``LinkCode``        calc    RO     link conditions bits 0-3, ports bits 4-7 (helper)
==================  ======  =====  ==============================================

A terminal is EDITABLE when ``DISP == 0`` and ``DISA != DISV`` and Channel Access
grants write access (the record semantics, as in pytmc ``effective_access()``).

Nothing here imports Qt or PyDM: the status of a terminal comes from any object with
the :class:`TerminalStatus` attributes (the live :class:`~.monitor.TerminalMonitor`).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

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

ACCESS_GRANTED = "State requests accepted (DISP == 0, DISA != DISV)"
READ_ONLY_NOTE = (
    "This PyDM session is read-only (Qt Designer or pydm --read-only): Channel Access write "
    "permission is not checked and state requests are disabled here."
)

# Tree filter modes, in the order of the "Show" combo box of the .ui
SHOW_ALL, SHOW_FAULTS, SHOW_NOT_OP, SHOW_LINK, SHOW_EDITABLE, SHOW_DISCONNECTED = range(6)


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


# -------------------------------------------------------------------- access
def access_rule(disp, disa, disv, write_access=None, read_only=False) -> tuple[str, list[str]]:
    """
    EDITABLE / LOCKED / UNKNOWN for one terminal, with the reasons when locked.

    EDITABLE when ``DISP == 0`` and ``DISA != DISV`` and write access is not denied.
    In a read-only PyDM session (``read_only``: Qt Designer, ``pydm --read-only``) every
    channel reports no write access regardless of the IOC, so write access is ignored
    there: the answer then comes from the record fields only.
    """
    if read_only:
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


def access_tooltip(access: str, reasons: list[str], read_only: bool = False) -> str:
    """Tooltip for an access value: the lock reasons, plus a note in read-only PyDM sessions."""
    text = f"{access}\n" + ("\n".join(reasons) if reasons else ACCESS_GRANTED)
    if read_only:
        text += f"\n\n{READ_ONLY_NOTE}"
    return text


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


# ------------------------------------------------------ roll-up and filtering
class TerminalStatus(Protocol):
    """What the roll-up and the filter read from a terminal (a TerminalMonitor provides it)."""

    terminal: Terminal
    state_text: str | None
    link_text: str | None
    health: int
    access: tuple[str, list[str]]


@dataclass(frozen=True)
class GroupSummary:
    """The worst status and the counts of a group of terminals (a group / Port row of the tree)."""

    total: int
    worst: int
    disconnected: int
    not_op: int
    bad_link: int
    editable: int
    unknown: int

    @classmethod
    def of(cls, terminals: list[TerminalStatus]) -> GroupSummary:
        accesses = [t.access[0] for t in terminals]
        return cls(
            total=len(terminals),
            worst=max((t.health for t in terminals), default=H_OK),
            disconnected=sum(t.health == H_DISCONNECTED for t in terminals),
            not_op=sum(t.state_text is not None and t.state_text != GOOD_STATE for t in terminals),
            bad_link=sum(t.link_text is not None and t.link_text != GOOD_LINK for t in terminals),
            editable=accesses.count("EDITABLE"),
            unknown=accesses.count("UNKNOWN"),
        )

    @property
    def state_text(self) -> str:
        return "DISCONNECTED" if self.disconnected else "ALL OP" if not self.not_op else f"{self.not_op} NOT OP"

    @property
    def link_text(self) -> str:
        return "DISCONNECTED" if self.disconnected else "ALL OK" if not self.bad_link else f"{self.bad_link} NOT OK"

    @property
    def state_tooltip(self) -> str:
        in_op = self.total - self.not_op - self.disconnected
        return f"{in_op} of {self.total} in OP, {self.not_op} not OP, {self.disconnected} disconnected"

    @property
    def access(self) -> str:
        """EDITABLE if any terminal is, UNKNOWN if none is known, else LOCKED."""
        return "EDITABLE" if self.editable else "UNKNOWN" if self.unknown == self.total else "LOCKED"


def matches(status: TerminalStatus, mode: int, text: str = "") -> bool:
    """Whether a terminal passes the tree filter: a ``SHOW_*`` mode and a lower-case text."""
    t = status.terminal
    if text and text not in f"{t.name} {t.type} {t.port}".lower():
        return False
    if mode == SHOW_FAULTS:
        return status.health != H_OK
    if mode == SHOW_NOT_OP:
        return status.state_text != GOOD_STATE
    if mode == SHOW_LINK:
        return status.link_text != GOOD_LINK
    if mode == SHOW_EDITABLE:
        return status.access[0] == "EDITABLE"
    if mode == SHOW_DISCONNECTED:
        return status.health == H_DISCONNECTED
    return True
