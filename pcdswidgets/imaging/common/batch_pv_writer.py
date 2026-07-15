"""Generic batch PV writer dialog with confirmation, verification, and undo."""

from __future__ import annotations

import logging
from dataclasses import dataclass

import epics
from qtpy.QtCore import Qt, QThread, Signal
from qtpy.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)


@dataclass
class PVChange:
    """One proposed PV write."""

    pv_name: str
    current_value: float | None
    new_value: float
    enabled: bool = True


class _VerifyWorker(QThread):
    """Writes PVs sequentially, then reads back to verify."""

    finished = Signal(object)  # dict[str, bool] pv_name -> success

    def __init__(
        self,
        changes: list[PVChange],
        write_timeout: float = 10.0,
        read_timeout: float = 2.0,
        parent=None,
    ):
        super().__init__(parent)
        self._changes = changes
        self._write_timeout = write_timeout
        self._read_timeout = read_timeout

    def run(self) -> None:
        results: dict[str, bool] = {}
        for change in self._changes:
            pv = change.pv_name
            try:
                ret = epics.caput(pv, change.new_value, wait=True, timeout=self._write_timeout)
                if ret is None or ret == -1:
                    results[pv] = False
                    continue
            except Exception:
                logger.exception("caput failed for %s", pv)
                results[pv] = False
                continue

            # Read back and verify
            try:
                readback = epics.caget(pv, timeout=self._read_timeout)
                if readback is None:
                    results[pv] = False
                else:
                    results[pv] = abs(float(readback) - change.new_value) < 0.5
            except Exception:
                logger.exception("caget verification failed for %s", pv)
                results[pv] = False

        self.finished.emit(results)


class _UndoWorker(QThread):
    """Reverts PVs to their previous values."""

    finished = Signal(bool)  # all reverted successfully

    def __init__(self, revert_map: dict[str, float], timeout: float = 10.0, parent=None):
        super().__init__(parent)
        self._revert_map = revert_map
        self._timeout = timeout

    def run(self) -> None:
        all_ok = True
        for pv, val in self._revert_map.items():
            try:
                ret = epics.caput(pv, val, wait=True, timeout=self._timeout)
                if ret is None or ret == -1:
                    all_ok = False
            except Exception:
                logger.exception("Undo caput failed for %s", pv)
                all_ok = False
        self.finished.emit(all_ok)


class BatchPVWriterDialog(QDialog):
    """Modal dialog that previews, writes, verifies, and optionally undoes PV changes.

    Parameters
    ----------
    changes : list[PVChange]
        Proposed writes to preview.
    parent : QWidget | None
        Parent widget.
    """

    COL_CHECK = 0
    COL_PV = 1
    COL_CURRENT = 2
    COL_ARROW = 3
    COL_NEW = 4
    COL_STATUS = 5
    NUM_COLS = 6

    def __init__(self, changes: list[PVChange], parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Confirm PV Changes")
        self.setMinimumWidth(500)
        self._changes = changes
        self._checkboxes: list[QCheckBox] = []
        self._worker: _VerifyWorker | None = None
        self._undo_worker: _UndoWorker | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        header = QLabel("<b>The following PVs will be written:</b>")
        layout.addWidget(header)

        # Table
        self._table = QTableWidget(len(self._changes), self.NUM_COLS)
        self._table.setHorizontalHeaderLabels(
            ["", "PV", "Current", "", "New", "Status"]
        )
        self._table.horizontalHeader().setSectionResizeMode(
            self.COL_PV, QHeaderView.Stretch
        )
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.setSelectionMode(QTableWidget.NoSelection)

        for row, entry in enumerate(self._changes):
            # Checkbox
            cb = QCheckBox()
            cb.setChecked(entry.enabled)
            self._checkboxes.append(cb)
            cb_widget = QWidget()
            cb_layout = QHBoxLayout(cb_widget)
            cb_layout.addWidget(cb)
            cb_layout.setAlignment(Qt.AlignCenter)
            cb_layout.setContentsMargins(0, 0, 0, 0)
            self._table.setCellWidget(row, self.COL_CHECK, cb_widget)

            # PV name
            self._table.setItem(row, self.COL_PV, QTableWidgetItem(entry.pv_name))

            # Current value
            cur_text = f"{entry.current_value:.0f}" if entry.current_value is not None else "?"
            self._table.setItem(row, self.COL_CURRENT, QTableWidgetItem(cur_text))

            # Arrow
            arrow = QTableWidgetItem("\u2192")
            arrow.setTextAlignment(Qt.AlignCenter)
            self._table.setItem(row, self.COL_ARROW, arrow)

            # New value
            self._table.setItem(
                row, self.COL_NEW, QTableWidgetItem(f"{entry.new_value:.0f}")
            )

            # Status (initially empty)
            self._table.setItem(row, self.COL_STATUS, QTableWidgetItem(""))

        # Resize columns
        self._table.setColumnWidth(self.COL_CHECK, 30)
        self._table.setColumnWidth(self.COL_ARROW, 30)
        self._table.setColumnWidth(self.COL_CURRENT, 70)
        self._table.setColumnWidth(self.COL_NEW, 70)
        self._table.setColumnWidth(self.COL_STATUS, 50)

        layout.addWidget(self._table)

        # Buttons
        self._buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self._buttons.accepted.connect(self._on_ok)
        self._buttons.rejected.connect(self.reject)
        layout.addWidget(self._buttons)

    def _on_ok(self) -> None:
        """Write enabled PVs, verify, then close or offer undo."""
        enabled = self._get_enabled_changes()
        if not enabled:
            self.accept()
            return

        # Disable UI during write
        self._buttons.setEnabled(False)
        for cb in self._checkboxes:
            cb.setEnabled(False)

        self._worker = _VerifyWorker(enabled, parent=self)
        self._worker.finished.connect(self._on_verify_done)
        self._worker.start()

    def _on_verify_done(self, results: dict[str, bool]) -> None:
        """Update status column and handle success/failure."""
        all_ok = True
        for row, entry in enumerate(self._changes):
            if not self._checkboxes[row].isChecked():
                continue
            status_item = self._table.item(row, self.COL_STATUS)
            if results.get(entry.pv_name, False):
                status_item.setText("\u2713")  # checkmark
                status_item.setForeground(Qt.green)
            else:
                status_item.setText("\u2717")  # X mark
                status_item.setForeground(Qt.red)
                all_ok = False

        if all_ok:
            self.accept()
        else:
            self._offer_undo_or_continue()

    def _offer_undo_or_continue(self) -> None:
        """Show message box allowing user to undo failed writes or continue."""
        msg = QMessageBox(self)
        msg.setWindowTitle("Write Verification Failed")
        msg.setText("Some PV writes could not be verified.")
        msg.setInformativeText("Undo will revert all PVs to their previous values.")
        undo_btn = msg.addButton("Undo All", QMessageBox.RejectRole)
        continue_btn = msg.addButton("Continue", QMessageBox.AcceptRole)
        msg.setDefaultButton(continue_btn)
        msg.exec_()

        if msg.clickedButton() == undo_btn:
            self._do_undo()
        else:
            self.accept()

    def _do_undo(self) -> None:
        """Revert all written PVs to their previous values."""
        revert_map: dict[str, float] = {}
        for row, entry in enumerate(self._changes):
            if self._checkboxes[row].isChecked() and entry.current_value is not None:
                revert_map[entry.pv_name] = entry.current_value

        if not revert_map:
            self.reject()
            return

        self._undo_worker = _UndoWorker(revert_map, parent=self)
        self._undo_worker.finished.connect(self._on_undo_done)
        self._undo_worker.start()

    def _on_undo_done(self, success: bool) -> None:
        if not success:
            logger.warning("Some PV reverts failed during undo")
        self.reject()

    def _get_enabled_changes(self) -> list[PVChange]:
        """Return the list of changes the user has left checked."""
        result: list[PVChange] = []
        for entry, cb in zip(self._changes, self._checkboxes):
            if cb.isChecked():
                result.append(entry)
        return result

    def get_enabled_changes(self) -> list[PVChange]:
        """Public accessor for enabled changes (after dialog accepted)."""
        return self._get_enabled_changes()
