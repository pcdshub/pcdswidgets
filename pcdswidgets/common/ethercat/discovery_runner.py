"""Runs the read-only EtherCAT discovery in the background for the ``common.ethercat`` widgets."""

from __future__ import annotations

import sys
from pathlib import Path

from qtpy import QtCore


class DiscoveryRunner(QtCore.QObject):
    """
    Runs ``python -m pcdswidgets.common.ethercat.discover <plc> -o <output>`` in the
    background, one run at a time. Started only by the user (the Rediscover button),
    never retried on its own.
    """

    finished = QtCore.Signal(object)  # the discovery file that was written (Path)
    failed = QtCore.Signal(str)  # the last lines of the output, or the exit code

    def __init__(self, parent: QtCore.QObject | None = None):
        super().__init__(parent)
        self._process: QtCore.QProcess | None = None

    @property
    def running(self) -> bool:
        return self._process is not None

    def start(self, plc: str, output: Path) -> bool:
        """Start a discovery of ``plc`` written to ``output``; False if one is running or no plc."""
        if self.running or not plc:
            return False
        process = QtCore.QProcess(self)
        process.setProcessChannelMode(QtCore.QProcess.MergedChannels)
        process.finished.connect(lambda code, _status: self._on_finished(code, output))
        self._process = process
        process.start(sys.executable, ["-m", "pcdswidgets.common.ethercat.discover", plc, "-o", str(output)])
        return True

    def _on_finished(self, code: int, output: Path):
        log = bytes(self._process.readAll()).decode(errors="replace").strip()
        self._process.deleteLater()
        self._process = None
        if code == 0 and output.is_file():
            self.finished.emit(output)
        else:
            self.failed.emit("\n".join(log.splitlines()[-6:]) if log else f"exit code {code}")
