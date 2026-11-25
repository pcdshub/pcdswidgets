"""
discoveryFile handling. A missing file is only explained: the read-only discovery runs
when the user presses Rediscover, never on its own. A directory or a not-yet-existing
file is then created. Uses a fake ``ads`` script (via ADS_ACTIONS_BIN) that only
answers ``read-ecat-topology``: no PLC, no ads-actions.
"""

import json
import os
import stat

import pytest

from pcdswidgets.common.ethercat import discover
from pcdswidgets.common.ethercat import ethercat_terminal_states_stretch as stretch_module
from pcdswidgets.common.ethercat.ethercat_terminal_states_stretch import EthercatTerminalStatesStretch

from .conftest import PREFIX, wait_until

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
    monkeypatch.setattr(discover, "CACHE_DIR", cache)
    return script


def make(qtbot, discovery_file: str) -> EthercatTerminalStatesStretch:
    states = EthercatTerminalStatesStretch()
    qtbot.addWidget(states)
    states.setProperty("plc", "plc-test")
    states.setProperty("prefix", PREFIX)
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


# ------------------------------------------------- discovery is a user action
def press_rediscover(states):
    assert states.rediscoverButton.isEnabled()
    states.rediscoverButton.click()


def test_missing_file_starts_nothing(qtbot, fake_ads, tmp_path):
    states = make(qtbot, str(tmp_path / "out"))
    qtbot.wait(500)
    assert not states.runner.running and states.monitors == {}
    assert not (tmp_path / "out").exists()
    text = states.terminalTree.topLevelItem(0).text(0)
    assert text.startswith("No discovery file") and "Press Rediscover" in text
    assert "pcdswidgets.common.ethercat.discover" in text  # the command-line alternative


def test_reload_never_discovers(qtbot, fake_ads, tmp_path):
    states = make(qtbot, str(tmp_path / "out"))
    for _ in range(3):
        states.reload()
    assert not states.runner.running and not (tmp_path / "out").exists()


def test_rediscover_creates_the_file(qtbot, fake_ads, tmp_path):
    """End to end once (the path variants are covered by test_resolve_output)."""
    created = tmp_path / "a" / "b" / "snap.json"  # missing parent directories too
    states = make(qtbot, str(created))
    assert not created.exists()
    press_rediscover(states)
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
        press_rediscover(states)
        wait_until(lambda: len(states.monitors) == 2, timeout=30)
        assert states.meta["_path"] == str(tmp_path / "cache" / "plc-test.json")
        states.teardown()
    finally:
        locked.chmod(stat.S_IRWXU)


def test_failed_discovery_is_reported(qtbot, fake_ads, tmp_path, monkeypatch):
    fake_ads.write_text("#!/bin/sh\necho 'route to plc-test missing' >&2\nexit 3\n")
    dialogs = []
    monkeypatch.setattr(stretch_module.QtWidgets.QMessageBox, "warning", lambda *a: dialogs.append(a))
    states = make(qtbot, str(tmp_path / "out"))
    press_rediscover(states)
    wait_until(lambda: not states.runner.running, timeout=30)
    assert len(dialogs) == 1 and "route to plc-test missing" in dialogs[0][2]
    assert states.terminalTree.topLevelItem(0).text(0).startswith("No discovery file")  # explanation restored
    assert states.rediscoverButton.isEnabled()  # the user can retry
    states.reload()
    assert not states.runner.running  # never retried on its own


def test_writable_output(tmp_path):
    """The discovery target if it can be written, else the user cache."""
    target = tmp_path / "a" / "snap.json"
    assert discover.writable_output(target, "plc-test") == target
    locked = tmp_path / "locked"
    locked.mkdir()
    locked.chmod(stat.S_IRUSR | stat.S_IXUSR)
    try:
        if os.access(locked, os.W_OK):
            pytest.skip("running as a user that can write read-only directories")
        assert discover.writable_output(locked / "snap.json", "plc-test") == discover.resolve_output(None, "plc-test")
    finally:
        locked.chmod(stat.S_IRWXU)
