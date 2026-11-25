"""Channel Access subscription to one EtherCAT terminal, shared by both ``common.ethercat`` widgets."""

from __future__ import annotations

import functools

from pydm.data_plugins import is_read_only
from pydm.widgets.channel import PyDMChannel
from qtpy import QtCore

from pcdswidgets.common.ethercat.constants import LINK_ENUM, STATE_ENUM
from pcdswidgets.common.ethercat.model import (
    GOOD_LINK,
    GOOD_STATE,
    H_DISCONNECTED,
    H_FAULT,
    H_OK,
    Terminal,
    access_rule,
    decode_link_text,
    decode_state_flags,
)


def session_read_only() -> bool:
    """True in a read-only PyDM session: Qt Designer, or ``pydm --read-only``."""
    return bool(is_read_only())


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
    state / link / access (a :class:`~.model.TerminalStatus`). Shared by both widgets.
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
        return access_rule(
            self.value("disp"), self.value("disa"), self.value("disv"), self.write_access, session_read_only()
        )
