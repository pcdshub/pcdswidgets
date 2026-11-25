"""
Live mode (ca://) with no IOC, the discovery wrapper (no ads-actions needed), and the
pcdswidgets-show screen. Nothing is written to EPICS and no ads command is run.
"""

import json

import pytest

from pcdswidgets.common.ethercat import discover
from pcdswidgets.generated.path_defs import SCREEN_PATHS, WIDGET_PATHS
from pcdswidgets.show_screen import main as show_main

from .conftest import DISCOVERY, PLC, make_states, select, wait


# ------------------------------------------------------------------ live
@pytest.fixture(scope="module")
def live_states(qapp):
    states = make_states(mock=False, prefix="PYTEST:NO:IOC:")
    wait(2.0)
    yield states
    states.teardown()
    states.close()
    states.deleteLater()


def test_live_uses_channel_access(live_states):
    assert live_states.protocol == "ca://"
    assert "(MOCK)" not in live_states.DeviceName.text()


def test_live_rows_disconnected(live_states):
    top = live_states.terminalTree.topLevelItem(0)
    assert (top.text(2), top.text(3)) == ("DISCONNECTED", "DISCONNECTED")
    assert all(m.health == 2 for m in live_states.monitors.values())
    assert all(m.access[0] == "UNKNOWN" for m in live_states.monitors.values())


def test_live_panel_disconnected(live_states):
    w = select(live_states, 1015)
    assert [w.PyDMLabel_rbv.text(), w.flagsLabel.text(), w.linkLabel.text()] == ["DISCONNECTED"] * 3
    assert w.accessLabel.text() == "UNKNOWN" and not w.requestFrame.isEnabled()


# --------------------------------------------------------------- designer
def test_unconfigured_widget_shows_hint(qtbot):
    """In designer, before any property is set: no PVs, no discovery, just a hint."""
    from pcdswidgets.common.ethercat.ethercat_terminal_states_stretch import EthercatTerminalStatesStretch

    states = EthercatTerminalStatesStretch()
    qtbot.addWidget(states)
    assert states.monitors == {}
    assert states.terminalTree.topLevelItem(0).text(0).startswith("Set the plc and prefix")
    assert not states.rediscoverButton.isEnabled()


def test_missing_discovery_file_explains(qtbot, tmp_path, monkeypatch):
    from pcdswidgets.common.ethercat import discover
    from pcdswidgets.common.ethercat import ethercat_terminal_states_stretch as module

    monkeypatch.setattr(discover, "CACHE_DIR", tmp_path)
    states = module.EthercatTerminalStatesStretch()
    qtbot.addWidget(states)
    states.setProperty("plc", "plc-does-not-exist")
    states.reload()
    text = states.terminalTree.topLevelItem(0).text(0)
    assert "No discovery file" in text and "pcdswidgets.common.ethercat.discover" in text


# ---------------------------------------------------------------- discover
def test_discover_refuses_non_read_only_commands():
    with pytest.raises(RuntimeError, match="refusing"):
        discover.run_ads("/bin/true", "request-ecat-state", [], timeout=1)


@pytest.mark.parametrize(
    "flags, enum",
    [
        (None, None),
        ([], "OK"),
        (["OK"], "OK"),
        (["NOT_PRESENT"], "NOT_PRESENT"),
        (["ADDITIONAL_LINK", "PORT_D"], "MULTIPLE_FLAGS"),
    ],
)
def test_link_enum_from_flags(flags, enum):
    assert discover.link_enum_from_flags(flags) == enum


def test_discover_builds_discovery_json(monkeypatch, tmp_path):
    """Feed a recorded-style topology through the wrapper (no ads-actions, no PLC)."""
    topology = {
        "slaves": [
            {"port": 1002, "device_name": "Term 2 (EK1122)", "terminal_type": "EK1122", "state": "OP",
             "link_flags": ["OK"], "port_neighbors": {"A": 1001, "B": 0, "C": 0, "D": 0}},
            {"port": 1001, "device_name": "Term 1 (EK1100)", "terminal_type": "EK1100", "state": "OP",
             "state_flags": ["ERROR"], "link_flags": ["ADDITIONAL_LINK", "PORT_D"],
             "port_neighbors": {"A": 0, "B": 1002, "C": 0, "D": 0}},
        ],
        "summary": {"summary_ports": [1001, 1002]},
    }  # fmt: skip
    calls = []

    def fake_run_ads(ads, subcommand, args, timeout):
        calls.append((subcommand, args))
        return "diagnostic line\n" + json.dumps(topology)

    monkeypatch.setattr(discover, "find_ads", lambda: "/fake/ads")
    monkeypatch.setattr(discover, "run_ads", fake_run_ads)
    output = tmp_path / "plc.json"
    assert discover.main(["plc-test", "-o", str(output)]) == 0
    assert calls == [("read-ecat-topology", ["plc-test", "--format", "json", "--port-end", "65535"])]
    data = json.loads(output.read_text())
    assert [t["port"] for t in data["terminals"]] == [1001, 1002]
    first = data["terminals"][0]
    assert first["snapshot"] == {
        "state": "OP",
        "link": "MULTIPLE_FLAGS",
        "state_flags": ["ERROR"],
        "link_flags": ["ADDITIONAL_LINK", "PORT_D"],
    }
    assert first["neighbors"] == {"A": 0, "B": 1002, "C": 0, "D": 0}


def test_snapshot_matches_discovery_schema():
    data = json.loads(DISCOVERY.read_text())
    assert data["schema"] == discover.SCHEMA_VERSION and data["plc"] == PLC
    assert data["sources"][0].startswith("ads read-ecat-topology")


# ------------------------------------------------------- pcdswidgets-show
def test_registered_screen_and_widgets():
    assert SCREEN_PATHS["ethercat_terminal_states"] == "screens/common/ethercat/ethercat_terminal_states.py"
    assert "EthercatTerminalStateDoubleRow" in WIDGET_PATHS
    assert "EthercatTerminalStatesStretch" in WIDGET_PATHS


def test_show_screen_help(capsys):
    with pytest.raises(SystemExit):
        show_main(["ethercat_terminal_states", "--help"])
    out = capsys.readouterr().out
    for macro in ("--PLC", "--PREFIX", "--DISCOVERY", "--MOCK", "--CONFIRM"):
        assert macro in out


def test_screen_display_from_macros(qtbot):
    from pydm.utilities import import_module_by_filename

    import pcdswidgets

    path = f"{pcdswidgets.__path__[0]}/{SCREEN_PATHS['ethercat_terminal_states']}"
    module = import_module_by_filename(path)
    display = module.EthercatTerminalStates(
        macros={"PLC": PLC, "PREFIX": "SCREEN:", "DISCOVERY": str(DISCOVERY), "MOCK": "1", "CONFIRM": "0"}
    )
    qtbot.addWidget(display)
    states = display.states
    assert (states.get_plc(), states.get_prefix(), states.get_mock(), states.get_confirm_requests()) == (
        PLC,
        "SCREEN:",
        True,
        False,
    )
    assert len(states.monitors) == 85
    assert display.windowTitle() == "EtherCAT Terminal States - plc-sds-raptor (MOCK)"
    states.teardown()
