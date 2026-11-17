"""Pure logic of pcdswidgets.common.ethercat: decoding, access/health rules, tree, mock seeds."""

import pytest

from pcdswidgets.common.ethercat import ethercat_state as es

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
    assert es.decode_link_text(code) == text


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
    assert es.decode_state_flags(raw) == flags


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
    got, why = es.access_rule(disp, disa, disv, write)
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
    assert es.Terminal(1, name, type_).display_name == shown


def _t(port, a=0, b=0, c=0, d=0, name=None):
    return es.Terminal(port, name or f"T{port}", "EL1004", neighbors={"A": a, "B": b, "C": c, "D": d})


def test_build_tree_chain_is_flat():
    groups = es.build_tree([_t(1, b=2), _t(2, a=1, b=3), _t(3, a=2)], topology=True)
    assert [g.label for g in groups] == ["Master line"]
    assert [n.terminal.port for n in groups[0].children] == [1, 2, 3]
    assert all(not n.children for n in groups[0].children)


def test_build_tree_junction_gets_port_branches():
    # 1 -> junction 2 with downstream ports C (3) and D (4 -> 5)
    terminals = [_t(1, b=2), _t(2, a=1, c=3, d=4), _t(3, a=2), _t(4, a=2, b=5), _t(5, a=4)]
    junction = es.build_tree(terminals, topology=True)[0].children[1]
    assert junction.terminal.port == 2
    assert [(b.kind, b.label) for b in junction.children] == [("branch", "Port C"), ("branch", "Port D")]
    assert [n.terminal.port for n in junction.children[1].children] == [4, 5]


def test_build_tree_hot_connect_and_standalone():
    terminals = [_t(1, b=2), _t(2, a=1), _t(10, b=11, name="Box"), _t(11, a=10), _t(20)]
    assert [g.label for g in es.build_tree(terminals, topology=True)] == [
        "Master line",
        "Box group",
        "Standalone terminals",
    ]


def test_build_tree_without_topology_is_flat():
    groups = es.build_tree([_t(p) for p in (3, 1, 2)], topology=False)
    assert [g.label for g in groups] == ["Configured terminals"]
    assert groups[0].count_terminals() == 3


def test_real_snapshot_tree():
    meta, terminals = es.load_discovery(DISCOVERY)
    assert meta["plc"] == PLC and len(terminals) == 85
    groups = es.build_tree(terminals, bool(meta.get("topology_available")))
    assert groups[0].label == "Master line"
    assert sum(g.count_terminals() for g in groups) == 85  # every terminal placed exactly once
    assert "Unplaced terminals" not in [g.label for g in groups]


# --------------------------------------------------------------------- mock
def test_mock_seeds_default_locked_and_overrides():
    _, terminals = es.load_discovery(DISCOVERY)
    plain = es.mock_seeds(terminals)
    assert all((s["disp"], s["disa"], s["disv"]) == (1, 1, 1) for s in plain.values())  # pytmc default deny
    seeds = es.mock_seeds(
        terminals,
        {
            "state": {"1020": "SAFEOP"},
            "access": {"1020": {"DISP": 0, "DISA": 0, "DISV": 1}},
            "state_flags": {"1020": ["ERROR"]},
        },
    )
    assert seeds[1020]["state"] == es.STATE_ENUM.index("SAFEOP")
    assert es.access_rule(seeds[1020]["disp"], seeds[1020]["disa"], seeds[1020]["disv"])[0] == "EDITABLE"
    assert es.decode_state_flags(seeds[1020]["raw"]) == ["ERROR"]


def test_mock_query_has_enum_strings():
    query = es.mock_query("state", {"state": 3})
    assert query.startswith("?type=int&init=3") and "'SAFEOP'" in query


# --------------------------------------------------------------- pixmaps
@pytest.mark.parametrize("health, color", [(es.H_OK, "#8d8d8d"), (es.H_FAULT, "#da1e28")])
def test_dot_pixmap_colors(qapp, health, color):
    image = es.dot_pixmap(health, 12).toImage()
    assert image.pixelColor(6, 6).name() == color


def test_disconnected_dot_is_hollow(qapp):
    image = es.dot_pixmap(es.H_DISCONNECTED, 12).toImage()
    assert image.pixelColor(6, 6).alpha() == 0
