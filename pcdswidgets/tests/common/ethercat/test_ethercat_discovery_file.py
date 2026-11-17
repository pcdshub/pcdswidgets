"""
discoveryFile handling: a directory or a not-yet-existing file is created by the
read-only discovery instead of erroring. Uses a fake ``ads`` script (via
ADS_ACTIONS_BIN) that only answers ``read-ecat-topology``: no PLC, no ads-actions.
"""

import json
import os
import stat

import pytest

from pcdswidgets.common.ethercat import discover
from pcdswidgets.common.ethercat import ethercat_terminal_states_stretch as stretch_module
from pcdswidgets.common.ethercat.ethercat_terminal_states_stretch import EthercatTerminalStatesStretch

from .conftest import wait_until

TOPOLOGY = {
    "slaves": [
        {"port": 1001, "device_name": "Term 1 (EK1100)", "terminal_type": "EK1100", "state": "OP",
         "link_flags": ["OK"], "port_neighbors": {"A": 0, "B": 1002, "C": 0, "D": 0}},
        {"port": 1002, "device_name": "Term 2 (EL1004)", "terminal_type": "EL1004", "state": "OP",
         "link_flags": ["OK"], "port_neighbors": {"A": 1001, "B": 0, "C": 0, "D": 0}},
    ]
}  # fmt: skip


@pytest.fixture
def fake_ads(tmp_path, monkeypatch):
    """A fake ads-actions CLI (read-ecat-topology only) and a private user cache."""
    script = tmp_path / "bin" / "ads"
    script.parent.mkdir()
    script.write_text(f"#!/bin/sh\n[ \"$1\" = read-ecat-topology ] || exit 9\necho '{json.dumps(TOPOLOGY)}'\n")
    script.chmod(script.stat().st_mode | stat.S_IXUSR)
    monkeypatch.setenv("ADS_ACTIONS_BIN", str(script))
    cache = tmp_path / "cache"
    monkeypatch.setattr(stretch_module, "CACHE_DIR", cache)
    monkeypatch.setattr(discover, "CACHE_DIR", cache)
    return script


def make(qtbot, discovery_file: str) -> EthercatTerminalStatesStretch:
    states = EthercatTerminalStatesStretch()
    qtbot.addWidget(states)
    states.setProperty("plc", "plc-test")
    states.setProperty("prefix", "PYTEST:DISC:")
    states.setProperty("discoveryFile", discovery_file)
    states.reload()
    return states


# --------------------------------------------------------------- resolution
@pytest.mark.parametrize(
    "given, expected",
    [
        ("", "CACHE/plc.json"),
        ("TMP/existing_dir", "TMP/existing_dir/plc.json"),
        ("TMP/new_dir/", "TMP/new_dir/plc.json"),
        ("TMP/no_suffix", "TMP/no_suffix/plc.json"),
        ("TMP/a/b/snap.json", "TMP/a/b/snap.json"),
    ],
)
def test_resolve_output(tmp_path, monkeypatch, given, expected):
    monkeypatch.setattr(discover, "CACHE_DIR", tmp_path / "cache")
    (tmp_path / "existing_dir").mkdir()
    sub = {"TMP": str(tmp_path), "CACHE": str(tmp_path / "cache")}
    for key, value in sub.items():
        given, expected = given.replace(key, value), expected.replace(key, value)
    assert discover.resolve_output(given, "plc") == discover.Path(expected)


def test_can_create(tmp_path):
    assert discover.can_create(tmp_path / "x" / "y" / "z.json")  # parents get created
    locked = tmp_path / "locked"
    locked.mkdir()
    locked.chmod(stat.S_IRUSR | stat.S_IXUSR)
    try:
        if os.access(locked, os.W_OK):
            pytest.skip("running as a user that can write read-only directories")
        assert not discover.can_create(locked / "new" / "z.json")
    finally:
        locked.chmod(stat.S_IRWXU)


def test_cli_accepts_a_directory(fake_ads, tmp_path):
    assert discover.main(["plc-cli", "-o", str(tmp_path / "out") + "/"]) == 0
    data = json.loads((tmp_path / "out" / "plc-cli.json").read_text())
    assert [t["port"] for t in data["terminals"]] == [1001, 1002]
    assert not list(tmp_path.glob("**/*.tmp"))


# ---------------------------------------------------------- widget creates
@pytest.mark.parametrize("kind", ["existing_dir", "dir_with_slash", "missing_file", "no_suffix"])
def test_missing_discovery_file_is_created(qtbot, fake_ads, tmp_path, kind):
    (tmp_path / "existing_dir").mkdir()
    given, created = {
        "existing_dir": (tmp_path / "existing_dir", tmp_path / "existing_dir" / "plc-test.json"),
        "dir_with_slash": (f"{tmp_path / 'new_dir'}/", tmp_path / "new_dir" / "plc-test.json"),
        "missing_file": (tmp_path / "a" / "b" / "snap.json", tmp_path / "a" / "b" / "snap.json"),
        "no_suffix": (tmp_path / "no_suffix", tmp_path / "no_suffix" / "plc-test.json"),
    }[kind]
    states = make(qtbot, str(given))
    assert states.terminalTree.topLevelItem(0).text(0).startswith(f"Creating {created}")
    wait_until(lambda: len(states.monitors) == 2, timeout=30)
    assert created.is_file() and states.meta["_path"] == str(created)
    assert not (tmp_path / "cache").exists()  # written where asked, not to the cache
    states.teardown()


def test_unwritable_location_falls_back_to_cache(qtbot, fake_ads, tmp_path):
    locked = tmp_path / "locked"
    locked.mkdir()
    locked.chmod(stat.S_IRUSR | stat.S_IXUSR)
    try:
        if os.access(locked, os.W_OK):
            pytest.skip("running as a user that can write read-only directories")
        states = make(qtbot, str(locked / "snap.json"))
        assert "is not writable" in states.terminalTree.topLevelItem(0).text(0)
        wait_until(lambda: len(states.monitors) == 2, timeout=30)
        assert states.meta["_path"] == str(tmp_path / "cache" / "plc-test.json")
        states.teardown()
    finally:
        locked.chmod(stat.S_IRWXU)


def test_no_automatic_discovery_in_designer(qtbot, fake_ads, tmp_path, monkeypatch):
    monkeypatch.setattr(stretch_module, "is_qt_designer", lambda: True)
    states = make(qtbot, str(tmp_path / "designer_dir"))
    qtbot.wait(500)
    assert states._process is None and states.monitors == {}
    assert "created when the screen runs" in states.terminalTree.topLevelItem(0).text(0)
    assert not (tmp_path / "designer_dir").exists()


def test_failed_automatic_discovery_is_reported_once(qtbot, fake_ads, tmp_path, monkeypatch):
    fake_ads.write_text("#!/bin/sh\necho 'route to plc-test missing' >&2\nexit 3\n")
    dialogs = []
    monkeypatch.setattr(stretch_module.QtWidgets.QMessageBox, "warning", lambda *a: dialogs.append(a))
    states = make(qtbot, str(tmp_path / "out"))
    wait_until(lambda: states._process is None and "Could not create" in states.terminalTree.topLevelItem(0).text(0))
    assert dialogs == []  # automatic first discovery: no modal dialog
    states.reload()  # a reload must not start the failing discovery again
    assert states._process is None
    assert "Press Rediscover to retry" in states.terminalTree.topLevelItem(0).text(0)
