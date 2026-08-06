"""
Originally generated from jinja template ui_main_widget.j2

This file can be safely edited to change the runtime behavior of the widget.
"""

import logging

from qtpy.QtGui import QIcon, QPixmap
from qtpy.QtWidgets import QSpinBox

try:
    from qtpy.QtCore import pyqtProperty
except ImportError:
    from qtpy.QtCore import Property as pyqtProperty  # type: ignore

from pcdswidgets.builder.designer_options import DesignerOptions
from pcdswidgets.generated.imaging.common.bin_control_full_base import BinControlFullBase
from pcdswidgets.icons.glyphs import CAM_COG, CHECK, X_CIRCLE
from pcdswidgets.imaging.common.batch_pv_writer import BatchPVWriterDialog, PVChange

logger = logging.getLogger(__name__)

DEFAULT_DEP_SIZE_X = [":ROI1:SizeX"]
DEFAULT_DEP_SIZE_Y = [":ROI1:SizeY"]


class BinControlFull(BinControlFullBase):
    """Hardware binning control widget.

    Spinbox edits enter bin edit mode; confirm writes BinX/BinY and rescales
    dependent size PVs. Cancel restores spinboxes from RBV.
    """

    designer_options = DesignerOptions(
        group="ECS Imaging Common",
        is_container=False,
        icon=CAM_COG,
    )

    bin_x_spinbox: QSpinBox
    bin_y_spinbox: QSpinBox

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._edit_mode: str | None = None

        self._dependent_pvs_size_x: list[str] = list(DEFAULT_DEP_SIZE_X)
        self._dependent_pvs_size_y: list[str] = list(DEFAULT_DEP_SIZE_Y)

        self._init_button_icons()
        self._connect_signals()

        self.bin_confirm_button.setVisible(False)
        self.bin_cancel_button.setVisible(False)

    # ── Properties ─────────────────────────────────────────────────────────

    @property
    def _in_edit_mode(self) -> bool:
        return self._edit_mode is not None

    # ── Setup ──────────────────────────────────────────────────────────────

    def _init_button_icons(self):
        for glyph, button in (
            (CHECK, self.bin_confirm_button),
            (X_CIRCLE, self.bin_cancel_button),
        ):
            icon = QIcon()
            icon.addPixmap(QPixmap(glyph), QIcon.Normal, QIcon.Off)
            button.setIcon(icon)

    def _connect_signals(self):
        self.bin_confirm_button.clicked.connect(self._on_bin_confirm)
        self.bin_cancel_button.clicked.connect(self._on_bin_cancel)
        self.sync_bins_checkbox.toggled.connect(self._on_sync_toggled)
        self.bin_x_spinbox.valueChanged.connect(self._on_bin_spinbox_edited)
        self.bin_y_spinbox.valueChanged.connect(self._on_bin_spinbox_edited)

    # ── RBV / spinbox helpers ───────────────────────────────────────────────

    def _rbv_value(self, label_name: str) -> float | None:
        label = getattr(self, label_name, None)
        if label is None:
            return None
        try:
            return float(label.text())
        except (ValueError, AttributeError):
            return None

    def _rbv_map(self) -> dict[str, float | None]:
        return {
            "bin_x": self._rbv_value("bin_x_rbv_label"),
            "bin_y": self._rbv_value("bin_y_rbv_label"),
        }

    def _spinbox_map(self) -> dict[str, QSpinBox]:
        return {
            "bin_x": self.bin_x_spinbox,
            "bin_y": self.bin_y_spinbox,
        }

    def _sync_spinboxes_from_hardware(self):
        """Set spinbox values from current RBV labels. Auto-check sync if bins match."""
        rbv = self._rbv_map()
        for key, spinbox in self._spinbox_map().items():
            val = rbv.get(key)
            if val is not None:
                spinbox.blockSignals(True)
                spinbox.setValue(int(val))
                spinbox.blockSignals(False)

        bin_x = rbv.get("bin_x")
        bin_y = rbv.get("bin_y")
        if bin_x is not None and bin_y is not None and int(bin_x) == int(bin_y):
            self.sync_bins_checkbox.blockSignals(True)
            self.sync_bins_checkbox.setChecked(True)
            self.sync_bins_checkbox.blockSignals(False)
            self.bin_y_spinbox.setEnabled(False)

    def _has_unsaved_changes(self) -> bool:
        rbv = self._rbv_map()
        for key, spinbox in self._spinbox_map().items():
            val = rbv.get(key)
            if val is not None and int(val) != spinbox.value():
                return True
        return False

    # ── Spinbox callbacks ──────────────────────────────────────────────────

    def _on_bin_spinbox_edited(self, _value=None):
        sender = self.sender()
        if sender is self.bin_x_spinbox and self.sync_bins_checkbox.isChecked():
            self.bin_y_spinbox.blockSignals(True)
            self.bin_y_spinbox.setValue(self.bin_x_spinbox.value())
            self.bin_y_spinbox.blockSignals(False)
        if not self._in_edit_mode:
            self._enter_bin_edit_mode()

    def _on_sync_toggled(self, checked: bool):
        self.bin_y_spinbox.setEnabled(not checked)
        if checked:
            self.bin_y_spinbox.setValue(self.bin_x_spinbox.value())

    # ── Edit mode ──────────────────────────────────────────────────────────

    def _enter_bin_edit_mode(self):
        self._edit_mode = "bin"
        self.bin_confirm_button.setVisible(True)
        self.bin_cancel_button.setVisible(True)

    def _exit_edit_mode(self):
        if not self._in_edit_mode:
            return
        self._edit_mode = None
        self.bin_confirm_button.setVisible(False)
        self.bin_cancel_button.setVisible(False)

    # ── Confirm / cancel ───────────────────────────────────────────────────

    def _on_bin_confirm(self):
        if not self.get_cam_prefix():
            return
        self._show_confirm_dialog()

    def _on_bin_cancel(self):
        rbv = self._rbv_map()
        for key in ("bin_x", "bin_y"):
            val = rbv.get(key)
            if val is not None:
                sb = self._spinbox_map()[key]
                sb.blockSignals(True)
                sb.setValue(int(val))
                sb.blockSignals(False)
        self._exit_edit_mode()

    # ── Write dialog ───────────────────────────────────────────────────────

    def _show_confirm_dialog(self) -> None:
        changes = self._build_change_list()
        if not changes:
            self._exit_edit_mode()
            return
        dialog = BatchPVWriterDialog(changes, parent=self)
        dialog.exec_()
        from qtpy.QtCore import QTimer
        QTimer.singleShot(500, self._after_write_sync)
        self._exit_edit_mode()

    def _build_change_list(self) -> list[PVChange]:
        prefix = self.get_cam_prefix()
        if not prefix:
            return []
        rbv = self._rbv_map()
        spinbox = self._spinbox_map()
        changes: list[PVChange] = []
        self._collect_direct_bin_changes(prefix, rbv, spinbox, changes)
        self._collect_bin_dependents(prefix, rbv, spinbox, changes)
        return changes

    def _collect_direct_bin_changes(
        self, prefix: str, rbv: dict, spinbox: dict, changes: list[PVChange]
    ) -> None:
        for key, suffix in (("bin_x", ":BinX"), ("bin_y", ":BinY")):
            rbv_val = rbv.get(key)
            sb_val = spinbox[key].value()
            if rbv_val is not None and int(rbv_val) != sb_val:
                changes.append(PVChange(
                    pv_name=f"{prefix}{suffix}",
                    change=float(sb_val - rbv_val),
                    is_multiply=False,
                ))

    def _collect_bin_dependents(
        self, prefix: str, rbv: dict, spinbox: dict, changes: list[PVChange]
    ) -> None:
        old_bin_x = rbv.get("bin_x") or 1
        new_bin_x = spinbox["bin_x"].value()
        old_bin_y = rbv.get("bin_y") or 1
        new_bin_y = spinbox["bin_y"].value()

        if int(old_bin_x) != new_bin_x:
            scale = old_bin_x / new_bin_x if new_bin_x != 0 else 1.0
            self._append_dependent_pv_changes(
                prefix, self._dependent_pvs_size_x, scale, True, changes
            )
        if int(old_bin_y) != new_bin_y:
            scale = old_bin_y / new_bin_y if new_bin_y != 0 else 1.0
            self._append_dependent_pv_changes(
                prefix, self._dependent_pvs_size_y, scale, True, changes
            )

    def _append_dependent_pv_changes(
        self,
        prefix: str,
        suffixes: list[str],
        change: float,
        is_multiply: bool,
        changes: list[PVChange],
    ) -> None:
        for suffix in suffixes:
            changes.append(PVChange(
                pv_name=f"{prefix}{suffix}",
                change=change,
                is_multiply=is_multiply,
            ))

    def _after_write_sync(self):
        self._sync_spinboxes_from_hardware()

    # ── Designer properties ────────────────────────────────────────────────

    def get_dependent_pvs_size_x(self) -> list[str]:
        return self._dependent_pvs_size_x

    def set_dependent_pvs_size_x(self, value: list[str]) -> None:
        self._dependent_pvs_size_x = value if value else []

    dependent_pvs_size_x = pyqtProperty(
        "QStringList", get_dependent_pvs_size_x, set_dependent_pvs_size_x
    )

    def get_dependent_pvs_size_y(self) -> list[str]:
        return self._dependent_pvs_size_y

    def set_dependent_pvs_size_y(self, value: list[str]) -> None:
        self._dependent_pvs_size_y = value if value else []

    dependent_pvs_size_y = pyqtProperty(
        "QStringList", get_dependent_pvs_size_y, set_dependent_pvs_size_y
    )
