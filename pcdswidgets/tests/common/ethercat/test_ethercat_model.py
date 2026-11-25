"""The Qt-free model of pcdswidgets.common.ethercat: decoding, access rule, tree, roll-up, filter."""

import subprocess
import sys
from types import SimpleNamespace

import pytest

from pcdswidgets.common.ethercat import model

from .conftest import DISCOVERY, PLC


# ------------------------------------------------------------------ decoding
@pytest.mark.parametrize(
    "code, text",
    [
        (None, None),
        (0x00, "OK"),
        (0x08 | 0x80, "ADDITIONAL_LINK \u00b7 port D"),
        (0x02 | 0x04 | 0x10 | 0x20, "LINK_WITHOUT_COMM + MISSING_LINK \u00b7 ports A, B"),
        (0x01, "NOT_PRESENT"),
        (0x10 | 0x40, "ports A, C"),
    ],
)
def test_decode_link_text(code, text):
    assert model.decode_link_text(code) == text


@pytest.mark.parametrize(
    "raw, flags",
    [
        (None, None),
        (0x08, []),  # OP, no flags
        (0x04 | 0x10, ["ERROR"]),  # SAFEOP + ERROR
        (0x02 | 0x10 | 0x40, ["ERROR", "INITCMD_ERROR"]),
        (0xF1, ["ERROR", "INVALID_VPRS", "INITCMD_ERROR", "DISABLED"]),
    ],
)
def test_decode_state_flags(raw, flags):
    assert model.decode_state_flags(raw) == flags


@pytest.mark.parametrize(
    "disp, disa, disv, write, access, reasons",
    [
        (0, 0, 1, True, "EDITABLE", []),
        (1, 0, 1, True, "LOCKED", ["DISP"]),
        (0, 1, 1, True, "LOCKED", ["DISA = DISV"]),
        (1, 1, 1, None, "LOCKED", ["DISP", "DISA = DISV"]),  # pytmc default
        (0, 0, 1, False, "LOCKED", ["write permission"]),
        (None, 0, 1, True, "UNKNOWN", ["not connected"]),
    ],
)
def test_access_rule(disp, disa, disv, write, access, reasons):
    """Editable = DISP == 0 AND DISA != DISV (record semantics) AND CA write access."""
    got, why = model.access_rule(disp, disa, disv, write)
    assert got == access
    assert len(why) == len(reasons) and all(r in w for r, w in zip(reasons, why, strict=True))


# --------------------------------------------------------------- terminals
@pytest.mark.parametrize(
    "name, type_, shown",
    [
        ("Term 71 (EP9128-1021)", "EP9128-1021", "Term 71"),
        ("RCC-E6 (EL3314)", "EL3314-0000", "RCC-E6"),  # ADS cuts the revision
        ("FEL-SIM", "EK1100", "FEL-SIM"),
        ("M3 Selector A Digital IO (EP233", "EP2338-0001", "M3 Selector A Digital IO"),  # 31-char cut
    ],
)
def test_display_name(name, type_, shown):
    assert model.Terminal(1, name, type_).display_name == shown


def _t(port, a=0, b=0, c=0, d=0, name=None):
    return model.Terminal(port, name or f"T{port}", "EL1004", neighbors={"A": a, "B": b, "C": c, "D": d})


def test_build_tree_chain_is_flat():
    groups = model.build_tree([_t(1, b=2), _t(2, a=1, b=3), _t(3, a=2)])
    assert [g.label for g in groups] == ["Master line"]
    assert [n.terminal.port for n in groups[0].children] == [1, 2, 3]
    assert all(not n.children for n in groups[0].children)


def test_build_tree_junction_gets_port_branches():
    # 1 -> junction 2 with downstream ports C (3) and D (4 -> 5)
    terminals = [_t(1, b=2), _t(2, a=1, c=3, d=4), _t(3, a=2), _t(4, a=2, b=5), _t(5, a=4)]
    junction = model.build_tree(terminals)[0].children[1]
    assert junction.terminal.port == 2
    assert [(b.kind, b.label) for b in junction.children] == [("branch", "Port C"), ("branch", "Port D")]
    assert [n.terminal.port for n in junction.children[1].children] == [4, 5]


def test_build_tree_hot_connect_and_standalone():
    terminals = [_t(1, b=2), _t(2, a=1), _t(10, b=11, name="Box"), _t(11, a=10), _t(20)]
    assert [g.label for g in model.build_tree(terminals)] == [
        "Master line",
        "Box group",
        "Standalone terminals",
    ]


def test_build_tree_without_neighbours_is_flat():
    groups = model.build_tree([_t(p) for p in (3, 1, 2)])  # every port A-D neighbour is 0
    assert [g.label for g in groups] == ["Configured terminals"]
    assert groups[0].count_terminals() == 3


def test_real_discovery_tree():
    meta, terminals = model.load_discovery(DISCOVERY)
    assert meta["plc"] == PLC and len(terminals) == 85
    groups = model.build_tree(terminals)
    assert groups[0].label == "Master line"
    assert sum(g.count_terminals() for g in groups) == 85  # every terminal placed exactly once
    assert "Unplaced terminals" not in [g.label for g in groups]


# --------------------------------------------------- roll-up and filtering
def _status(port, state="OP", link="OK", health=model.H_OK, access="LOCKED", name=None):
    """A stand-in TerminalStatus (what a TerminalMonitor provides), no Qt needed."""
    return SimpleNamespace(
        terminal=_t(port, name=name), state_text=state, link_text=link, health=health, access=(access, [])
    )


def test_group_summary_all_ok():
    summary = model.GroupSummary.of([_status(1), _status(2)])
    assert (summary.state_text, summary.link_text, summary.access, summary.worst) == (
        "ALL OP",
        "ALL OK",
        "LOCKED",
        model.H_OK,
    )


def test_group_summary_counts_faults_and_editable():
    summary = model.GroupSummary.of(
        [
            _status(1, state="SAFEOP", health=model.H_FAULT, access="EDITABLE"),
            _status(2, link="MISSING_LINK", health=model.H_FAULT),
            _status(3, state="PREOP", link="NOT_PRESENT", health=model.H_FAULT),
        ]
    )
    assert (summary.state_text, summary.link_text, summary.access) == ("2 NOT OP", "2 NOT OK", "EDITABLE")
    assert summary.worst == model.H_FAULT
    assert summary.state_tooltip == "1 of 3 in OP, 2 not OP, 0 disconnected"


def test_group_summary_disconnected_wins():
    summary = model.GroupSummary.of(
        [_status(1), _status(2, state=None, link=None, health=model.H_DISCONNECTED, access="UNKNOWN")]
    )
    assert (summary.state_text, summary.link_text, summary.worst) == (
        "DISCONNECTED",
        "DISCONNECTED",
        model.H_DISCONNECTED,
    )
    assert model.GroupSummary.of([_status(1, access="UNKNOWN")]).access == "UNKNOWN"


@pytest.mark.parametrize(
    "mode, text, expected",
    [
        (model.SHOW_ALL, "", [1, 2, 3, 4]),
        (model.SHOW_FAULTS, "", [2, 3, 4]),
        (model.SHOW_NOT_OP, "", [2, 4]),
        (model.SHOW_LINK, "", [3, 4]),
        (model.SHOW_EDITABLE, "", [2]),
        (model.SHOW_DISCONNECTED, "", [4]),
        (model.SHOW_ALL, "rcc", [2, 3]),  # name, type or port, lower case
        (model.SHOW_FAULTS, "term", [4]),  # text and mode together
        (model.SHOW_ALL, "3", [3]),  # port
    ],
)
def test_matches(mode, text, expected):
    statuses = [
        _status(1, name="Coupler"),
        _status(2, state="SAFEOP", health=model.H_FAULT, access="EDITABLE", name="RCC-E6"),
        _status(3, link="MISSING_LINK", health=model.H_FAULT, name="RCC-E7"),
        _status(4, state=None, link=None, health=model.H_DISCONNECTED, access="UNKNOWN", name="Term 1004"),
    ]
    assert [s.terminal.port for s in statuses if model.matches(s, mode, text)] == expected


def test_model_needs_no_qt():
    """The model (and the discovery CLI) import neither Qt nor PyDM."""
    code = (
        "import sys; import pcdswidgets.common.ethercat.model, pcdswidgets.common.ethercat.discover; "
        "print(sorted(m for m in ('qtpy', 'PyQt5', 'pydm') if m in sys.modules))"
    )
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True)
    assert result.stdout.strip() == "[]"
