"""Read/write handle to a single PV via PyDM's channel plugin"""

from pydm.widgets.channel import PyDMChannel
from qtpy.QtCore import QObject, QTimer, Signal

# A brand-new PyDMChannel's first connect can silently never call connection_slot;
_CONNECT_RETRY_INTERVAL_MS = 2000
_CONNECT_RETRY_MAX_ATTEMPTS = 5


class PVChannel(QObject):
    """Read/write handle to a PV via PyDM's channel plugin.

    PyDMChannel is the plain object every PyDM widget already uses
    internally to talk to the CA/PVA plugin; using it directly avoids
    creating a widget purely to read or write a PV.
    """

    _value_signal = Signal(float)

    def __init__(self, parent=None, value_slot=None, connection_slot=None):
        super().__init__(parent)
        self._value_slot = value_slot
        self._connection_slot = connection_slot
        self._channel: PyDMChannel | None = None
        self._address: str | None = None
        self._got_connection_update = False
        self._retry_attempt = 0
        self._retry_timer = QTimer(self)
        self._retry_timer.setSingleShot(True)
        self._retry_timer.timeout.connect(self._retry_if_still_silent)

    def set_address(self, address: str) -> None:
        if self._address == address:
            return
        if self._channel is not None:
            self._channel.disconnect()
        self._address = address
        self._connect(attempt=1)

    def _connect(self, attempt: int) -> None:
        self._got_connection_update = False
        self._retry_attempt = attempt
        self._channel = PyDMChannel(
            address=self._address,
            value_signal=self._value_signal,
            value_slot=self._value_slot,
            connection_slot=self._on_connection_changed,
        )
        self._channel.connect()
        if attempt < _CONNECT_RETRY_MAX_ATTEMPTS:
            self._retry_timer.start(_CONNECT_RETRY_INTERVAL_MS)

    def _retry_if_still_silent(self) -> None:
        """Reconnect with a fresh channel if connection_slot never fired at all."""
        if self._got_connection_update:
            return
        self._channel.disconnect()
        self._connect(attempt=self._retry_attempt + 1)

    def _on_connection_changed(self, connected: bool) -> None:
        self._got_connection_update = True
        if self._connection_slot is not None:
            self._connection_slot(connected)

    def write(self, value: float) -> None:
        self._value_signal.emit(value)
