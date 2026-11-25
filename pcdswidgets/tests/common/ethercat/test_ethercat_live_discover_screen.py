"""
Never-connected widgets (an unreachable IOC), the discovery wrapper (no ads-actions
needed), and the pcdswidgets-show screen. Offline: no Channel Access, no ads command.
"""

import json

import pytest

from pcdswidgets.common.ethercat import discover
from pcdswidgets.generated.path_defs import SCREEN_PATHS, WIDGET_PATHS
from pcdswidgets.show_screen import main as show_main

from .conftest import DISCOVERY, PLC, PREFIX, make_states


# --------------------------------------------------------- never connected
@pytest.fixture(scope="module")
def unfed_states(qapp):
    """Every channel opened, no value ever arrives: what an unreachable IOC looks like."""
    states = make_states(fed=False)
    yield states
    states.teardown()
    states.close()
    states.deleteLater()


def test_unfed_rows_disconnected(unfed_states):
    top = unfed_states.terminalTree.topLevelItem(0)
    assert (top.text(2), top.text(3)) == ("DISCONNECTED", "DISCONNECTED")
    assert all(m.health == 2 for m in unfed_states.monitors.values())
    assert all(m.access[0] == "UNKNOWN" for m in unfed_states.monitors.values())


# --------------------------------------------------------------- designer
def test_unconfigured_widget_shows_hint(qtbot):
    """In designer, before any property is set: no PVs, no discovery, just a hint."""
    from pcdswidgets.common.ethercat.ethercat_terminal_states_stretch import EthercatTerminalStatesStretch

    states = EthercatTerminalStatesStretch()
    qtbot.addWidget(states)
    assert states.monitors == {}
    assert states.terminalTree.topLevelItem(0).text(0).startswith("Set the plc and prefix")
    assert not states.rediscoverButton.isEnabled()


# ---------------------------------------------------------------- discover
def test_discover_refuses_non_read_only_commands():
    with pytest.raises(RuntimeError, match="refusing"):
        discover.run_ads("/bin/true", "request-ecat-state", [], timeout=1)


DISCOVERY_KEYS = {"schema", "plc", "generated", "sources", "terminals"}
TERMINAL_KEYS = {"port", "name", "type", "neighbors"}


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
    assert discover.main(["plc-test", "-o", f"{tmp_path / 'new_dir'}/"]) == 0  # a directory: <dir>/<plc>.json
    output = tmp_path / "new_dir" / "plc-test.json"
    assert not list(tmp_path.glob("**/*.tmp"))  # written atomically
    assert calls == [("read-ecat-topology", ["plc-test", "--format", "json", "--port-end", "65535"])]
    data = json.loads(output.read_text())
    assert set(data) == DISCOVERY_KEYS
    assert [t["port"] for t in data["terminals"]] == [1001, 1002]
    first = data["terminals"][0]
    assert first == {
        "port": 1001,
        "name": "Term 1 (EK1100)",
        "type": "EK1100",
        "neighbors": {"A": 0, "B": 1002, "C": 0, "D": 0},
    }


def test_test_data_matches_discovery_format():
    """The test discovery file has exactly what discover.py writes (states are test-only data)."""
    data = json.loads(DISCOVERY.read_text())
    assert set(data) == DISCOVERY_KEYS and all(set(t) == TERMINAL_KEYS for t in data["terminals"])
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
    for macro in ("--PLC", "--PREFIX", "--DISCOVERY", "--CONFIRM"):
        assert macro in out
    assert "--MOCK" not in out


def test_screen_display_from_macros(qtbot):
    from pydm.utilities import import_module_by_filename

    import pcdswidgets

    path = f"{pcdswidgets.__path__[0]}/{SCREEN_PATHS['ethercat_terminal_states']}"
    module = import_module_by_filename(path)
    display = module.EthercatTerminalStates(
        macros={"PLC": PLC, "PREFIX": PREFIX, "DISCOVERY": str(DISCOVERY), "CONFIRM": "0"}
    )
    qtbot.addWidget(display)
    states = display.states
    assert (states.get_plc(), states.get_prefix(), states.get_confirm_requests()) == (PLC, PREFIX, False)
    assert len(states.monitors) == 85
    assert display.windowTitle() == "EtherCAT Terminal States - plc-sds-raptor"
    states.teardown()
