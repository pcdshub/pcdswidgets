"""Modal confirmation dialog for previewing PV changes before writing."""

from __future__ import annotations

from dataclasses import dataclass, field

from qtpy.QtCore import Qt
from qtpy.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


@dataclass
class ChangeEntry:
    """One proposed PV write."""

    pv_name: str
    current_value: float | None
    new_value: float
    enabled: bool = True
    category: str = ""  # "bin" | "roi" | "dependent"


class CropConfirmDialog(QDialog):
    """Modal preview of all PV changes before writing.

    Parameters
    ----------
    changes : list[ChangeEntry]
        Proposed writes to preview.
    parent : QWidget | None
        Parent widget.
    """

    COL_CHECK = 0
    COL_PV = 1
    COL_CURRENT = 2
    COL_ARROW = 3
    COL_NEW = 4
    COL_CATEGORY = 5
    NUM_COLS = 6

    def __init__(self, changes: list[ChangeEntry], parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Confirm PV Changes")
        self.setMinimumWidth(500)
        self._changes = changes
        self._checkboxes: list[QCheckBox] = []
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        header = QLabel("<b>The following PVs will be written:</b>")
        layout.addWidget(header)

        # Table
        self._table = QTableWidget(len(self._changes), self.NUM_COLS)
        self._table.setHorizontalHeaderLabels(
            ["", "PV", "Current", "", "New", "Category"]
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

            # Category
            self._table.setItem(
                row, self.COL_CATEGORY, QTableWidgetItem(entry.category)
            )

        # Resize columns
        self._table.setColumnWidth(self.COL_CHECK, 30)
        self._table.setColumnWidth(self.COL_ARROW, 30)
        self._table.setColumnWidth(self.COL_CURRENT, 70)
        self._table.setColumnWidth(self.COL_NEW, 70)
        self._table.setColumnWidth(self.COL_CATEGORY, 80)

        layout.addWidget(self._table)

        # Info note
        note = QLabel(
            "<i>Writes execute sequentially: bin \u2192 size \u2192 position \u2192 dependent (X before Y)</i>"
        )
        note.setWordWrap(True)
        layout.addWidget(note)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_enabled_changes(self) -> list[ChangeEntry]:
        """Return the list of changes the user has left checked."""
        result: list[ChangeEntry] = []
        for entry, cb in zip(self._changes, self._checkboxes):
            if cb.isChecked():
                result.append(entry)
        return result
