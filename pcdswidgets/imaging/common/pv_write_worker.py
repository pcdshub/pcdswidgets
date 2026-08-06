"""
QThread workers needed for sequential PV writes via EPICS CA.
"""

from __future__ import annotations

import logging

import epics
from qtpy.QtCore import QThread, Signal

logger = logging.getLogger(__name__)


class PVWriteWorker(QThread):
    """Executes an ordered sequence of PV writes, each with wait=True.

    Signals
    -------
    progress : (pv_name: str, success: bool)
        Emitted after each write attempt.
    finished_all : (success: bool)
        Emitted when the full sequence completes (True if all succeeded).
    """

    progress = Signal(str, bool)
    finished_all = Signal(bool)

    def __init__(
        self,
        write_sequence: list[tuple[str, float]],
        timeout: float = 10.0,
        parent=None,
    ):
        """
        Parameters
        ----------
        write_sequence : list of (pv_name, value) tuples
            Writes are executed in order. Each write blocks until acknowledged.
        timeout : float
            Timeout per individual caput call.
        """
        super().__init__(parent)
        self._sequence = write_sequence
        self._timeout = timeout
        self._stop = False

    def stop(self) -> None:
        self._stop = True

    def run(self) -> None:
        all_ok = True
        for pv_name, value in self._sequence:
            if self._stop:
                all_ok = False
                break
            try:
                result = epics.caput(pv_name, value, wait=True, timeout=self._timeout)
                success = result is not None and result != -1
            except Exception:
                logger.exception("caput failed for %s", pv_name)
                success = False

            if not success:
                logger.warning("Write failed: %s = %s", pv_name, value)
                all_ok = False

            self.progress.emit(pv_name, success)

        self.finished_all.emit(all_ok)
