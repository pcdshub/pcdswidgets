"""
Originally generated from jinja template ui_main_widget.j2

This file can be safely edited to change the runtime behavior of the widget.
"""

import logging

from pydm.widgets import PyDMImageView
from qtpy.QtCore import QPointF, Qt
from qtpy.QtGui import QColor, QIcon, QPixmap
from qtpy.QtWidgets import QPushButton, QSpinBox

try:
    from qtpy.QtCore import pyqtProperty
except ImportError:
    from qtpy.QtCore import Property as pyqtProperty  # type: ignore

from pcdswidgets.builder.designer_options import DesignerOptions
from pcdswidgets.generated.imaging.common.crop_and_bin_full_base import CropAndBinFullBase
from pcdswidgets.icons.glyphs import (
    CAM_COG,
    CHECK,
    MOVE,
    PEN_TOOL,
    TRASH,
    X_CIRCLE,
)
from pcdswidgets.imaging.common.cam_roi import CamROI
from pcdswidgets.imaging.common.coordinate_transform import CoordinateTransform
from pcdswidgets.imaging.common.batch_pv_writer import BatchPVWriterDialog, PVChange
from pcdswidgets.imaging.common.pv_write_worker import PVReadWorker

logger = logging.getLogger(__name__)

DEFAULT_CROP_BOX_COLOR = "green"

# Default dependent PV suffixes, overwritten in designer
# these PVs get overwritten if global crop/bin settings are changed
DEFAULT_DEP_X = [":ROI1:MinX", ":Over1:5:PositionX", ":Over1:6:PositionX",
                 ":Over1:7:PositionX", ":Over1:8:PositionX"]
DEFAULT_DEP_Y = [":ROI1:MinY", ":Over1:5:PositionY", ":Over1:6:PositionY",
                 ":Over1:7:PositionY", ":Over1:8:PositionY"]
DEFAULT_DEP_SIZE_X = [":ROI1:SizeX"]
DEFAULT_DEP_SIZE_Y = [":ROI1:SizeY"]

# Default coordinate transform PVs (drawing overlays on the screen)
DEFAULT_X_START ="IMAGE1:ROI:MinX_RBV"
DEFAULT_Y_START = "IMAGE1:ROI:MinY_RBV"
DEFAULT_BIN_X = ":IMAGE1:ROI:BinX"
DEFAULT_BIN_Y = ":IMAGE1:ROI:BinY"


class CropAndBinFull(CropAndBinFullBase):
    """Hardware crop-and-bin control widget.

    Provides spinbox-based editing of MinX/MinY/SizeX/SizeY and BinX/BinY.
    Spinboxes are decoupled from PVs — changes are previewed in a confirmation
    dialog and written sequentially via a worker thread.
    """

    designer_options = DesignerOptions(
        group="ECS Imaging Common",
        is_container=False,
        icon=CAM_COG
    )

    reset_roi_button: QPushButton
    confirm_button: QPushButton
    draw_button: QPushButton
    move_button: QPushButton
    cancel_button: QPushButton

    bin_x_spinbox: QSpinBox
    bin_y_spinbox: QSpinBox
    roi_x_spinbox: QSpinBox
    roi_y_spinbox: QSpinBox
    roi_width_spinbox: QSpinBox
    roi_height_spinbox: QSpinBox

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._image_view: PyDMImageView | None = None
        self._view_box = None
        self._draw_origin: QPointF | None = None
        self._in_edit_mode = False
        self._read_worker: PVReadWorker | None = None
        self._syncing_roi = False  # guard for ROI ↔ spinbox feedback loop

        # RBV snapshot captured on edit-mode entry
        self._rbv_snapshot: dict[str, int] = {}

        # Dependent PV suffix lists
        self._dependent_pvs_x: list[str] = list(DEFAULT_DEP_X)
        self._dependent_pvs_y: list[str] = list(DEFAULT_DEP_Y)
        self._dependent_pvs_size_x: list[str] = list(DEFAULT_DEP_SIZE_X)
        self._dependent_pvs_size_y: list[str] = list(DEFAULT_DEP_SIZE_Y)

        self._crop_box_color: QColor = QColor(DEFAULT_CROP_BOX_COLOR)
        self.roi_rect = CamROI(self._crop_box_color, 2, self)

        self._init_button_icons()
        self._connect_signals()

        # Initial visibility: only spinboxes + tools + trash visible
        self.roi_tools_row.setVisible(False)
        self.confirm_button.setVisible(False)
        self.cancel_button.setVisible(False)

    # ── Setup ─────────────────────────────────────────────────────────────

    def _init_button_icons(self):
        icon_map = {
            TRASH: self.reset_roi_button,
            MOVE: self.move_button,
            PEN_TOOL: self.draw_button,
            CHECK: self.confirm_button,
            X_CIRCLE: self.cancel_button,
        }
        for path, button in icon_map.items():
            icon = QIcon()
            icon.addPixmap(QPixmap(path), QIcon.Normal, QIcon.Off)
            button.setIcon(icon)

    def _connect_signals(self):
        # buttons
        self.reset_roi_button.clicked.connect(self._on_reset)
        self.confirm_button.clicked.connect(self._on_confirm)
        self.cancel_button.clicked.connect(self._on_cancel)
        self.move_button.clicked.connect(self._on_move_toggle)
        self.draw_button.clicked.connect(self._on_draw_toggle)

        # spinboxes
        self.sync_bins_checkbox.toggled.connect(self._on_sync_toggled)
        self.bin_x_spinbox.valueChanged.connect(self._on_spinbox_edited)
        self.bin_y_spinbox.valueChanged.connect(self._on_spinbox_edited)
        self.roi_x_spinbox.valueChanged.connect(self._on_spinbox_edited)
        self.roi_y_spinbox.valueChanged.connect(self._on_spinbox_edited)
        self.roi_width_spinbox.valueChanged.connect(self._on_spinbox_edited)
        self.roi_height_spinbox.valueChanged.connect(self._on_spinbox_edited)

        # user changes ROI with MOVE
        self.roi_rect.sigRegionChanged.connect(self._on_roi_changed)

    def link_parent_widgets(self, parent) -> None:
        """
        Attach ROI overlay to parent's PyDMImageView ViewBox.

        Called by parent on adoption
        """

        if hasattr(parent, "image_view"):
            self._image_view = parent.image_view
        else:
            return
        try:
            plot_item = self._image_view.getView()
            self._view_box = plot_item.getViewBox()
        except Exception:
            logger.error("Could not get ViewBox for crop overlay")
            return
        self._view_box.addItem(self.roi_rect)
        self._view_box.scene().sigMouseClicked.connect(self._on_scene_clicked)
        self._view_box.scene().sigMouseMoved.connect(self._on_scene_moved)

    def after_set_macro(self, macro_name: str, value: str) -> None:
        """Sync spinbox values from RBV labels once cam_prefix is set."""
        if macro_name == "cam_prefix" and value:
            self._sync_spinboxes_from_hardware()

    # ── RBV Helpers ────────────────────────────────────────────────────────

    def _rbv_value(self, label_name: str) -> float | None:
        """Read current numeric value from a PyDMLabel's displayed text."""
        label = getattr(self, label_name, None)
        if label is None:
            return None
        try:
            return float(label.text())
        except (ValueError, AttributeError):
            return None

    def _rbv_map(self) -> dict[str, float | None]:
        """Map spinbox names to their current RBV label values."""
        return {
            "bin_x": self._rbv_value("bin_x_rbv_label"),
            "bin_y": self._rbv_value("bin_y_rbv_label"),
            "roi_x": self._rbv_value("roi_x_rbv_label"),
            "roi_y": self._rbv_value("roi_y_rbv_label"),
            "roi_width": self._rbv_value("roi_width_rbv_label"),
            "roi_height": self._rbv_value("roi_height_rbv_label"),
        }

    def _spinbox_map(self) -> dict[str, int]:
        """Map spinbox names to their current spinbox values."""
        return {
            "bin_x": self.bin_x_spinbox,
            "bin_y": self.bin_y_spinbox,
            "roi_x": self.roi_x_spinbox,
            "roi_y": self.roi_y_spinbox,
            "roi_width": self.roi_width_spinbox,
            "roi_height": self.roi_height_spinbox,
        }

    def _sync_spinboxes_from_hardware(self):
        """Set spinbox values from current RBV labels."""
        rbv = self._rbv_map()

        for key, spinbox in self._spinbox_map().items():
            val = rbv.get(key)
            if val is not None:
                spinbox:QSpinBox
                spinbox.blockSignals(True)
                spinbox.setValue(int(val))
                spinbox.blockSignals(False)

    def _on_spinbox_edited(self, _value=None):
        """Called on any spinbox valueChanged — sync bins, manage edit mode, update ROI."""
        # handle syncing X and Y bins together
        sender = self.sender()
        if sender is self.bin_x_spinbox and self.sync_bins_checkbox.isChecked():
            self.bin_y_spinbox.blockSignals(True)
            self.bin_y_spinbox.setValue(self.bin_x_spinbox.value())
            self.bin_y_spinbox.blockSignals(False)

        #trigger edit mode if values are changed
        if self._in_edit_mode:
            self._sync_roi_from_spinboxes()
        else:
            self._enter_edit_mode()

    def _on_sync_toggled(self, checked: bool):
        self.bin_y_spinbox.setEnabled(not checked)
        if checked:
            self.bin_y_spinbox.setValue(self.bin_x_spinbox.value())

    # ── Confirm / Write ────────────────────────────────────────────────────

    def _on_confirm(self):
        """Initiate the confirm flow: read dependent PVs, then show dialog."""
        prefix = self.get_cam_prefix()
        if not prefix:
            return

        # Collect which dependent PVs we need to read
        dep_pvs = self._get_dependent_pv_names(prefix)
        if not dep_pvs:
            # No dependent PVs to read — go straight to dialog
            self._show_confirm_dialog({})
            return

        # Launch background read, then show dialog on completion
        self._set_controls_enabled(False)
        self._read_worker = PVReadWorker(dep_pvs, parent=self)
        self._read_worker.finished.connect(self._on_dep_reads_done)
        self._read_worker.start()

    def _get_dependent_pv_names(self, prefix: str) -> list[str]:
        """Determine which dependent PVs need reading based on current changes."""
        rbv = self._rbv_map()
        spinbox = self._spinbox_map()
        pvs: list[str] = []

        delta_x = spinbox["roi_x"] - int(rbv.get("roi_x") or 0)
        delta_y = spinbox["roi_y"] - int(rbv.get("roi_y") or 0)
        if delta_x != 0:
            pvs.extend(f"{prefix}{s}" for s in self._dependent_pvs_x)
        if delta_y != 0:
            pvs.extend(f"{prefix}{s}" for s in self._dependent_pvs_y)

        old_bin_x = int(rbv.get("bin_x") or 1)
        old_bin_y = int(rbv.get("bin_y") or 1)
        if old_bin_x != spinbox["bin_x"]:
            pvs.extend(f"{prefix}{s}" for s in self._dependent_pvs_size_x)
        if old_bin_y != spinbox["bin_y"]:
            pvs.extend(f"{prefix}{s}" for s in self._dependent_pvs_size_y)

        return pvs

    def _on_dep_reads_done(self, read_values: dict[str, float | None]) -> None:
        """Called when PVReadWorker finishes; show the confirmation dialog."""
        self._set_controls_enabled(True)
        self._show_confirm_dialog(read_values)

    def _show_confirm_dialog(self, dep_values: dict[str, float | None]) -> None:
        """Build change list and present modal confirmation dialog."""
        changes = self._build_change_list(dep_values)
        if not changes:
            self._exit_edit_mode()
            return

        # Order changes for sequential write (bin -> size -> position -> dependent)
        changes = self._order_change_list(changes)

        dialog = BatchPVWriterDialog(changes, parent=self)
        result = dialog.exec_()

        # Dialog handles writes + verification internally.
        # On accept (success or user chose continue), sync and exit.
        # On reject (cancel or undo), just exit edit mode.
        from qtpy.QtCore import QTimer
        QTimer.singleShot(500, self._after_write_sync)
        self._exit_edit_mode()

    def _build_change_list(self, dep_values: dict[str, float | None]) -> list[PVChange]:
        """Build the full list of proposed changes (direct + dependent)."""
        prefix = self.get_cam_prefix()
        if not prefix:
            return []

        rbv = self._rbv_map()
        spinbox = self._spinbox_map()
        changes: list[PVChange] = []

        # Direct changes
        self._collect_direct_changes(prefix, rbv, spinbox, changes)
        # Dependent offset propagation
        self._collect_offset_dependents(prefix, rbv, spinbox, dep_values, changes)
        # Dependent bin-size scaling
        self._collect_bin_dependents(prefix, rbv, spinbox, dep_values, changes)

        return changes

    def _collect_direct_changes(
        self, prefix: str, rbv: dict, spinbox: dict, changes: list[PVChange]
    ) -> None:
        pv_suffix = {
            "bin_x": ":BinX", "bin_y": ":BinY",
            "roi_x": ":MinX", "roi_y": ":MinY",
            "roi_width": ":SizeX", "roi_height": ":SizeY",
        }
        for key, suffix in pv_suffix.items():
            rbv_val = rbv.get(key)
            sb_val = spinbox[key]
            if rbv_val is not None and int(rbv_val) != sb_val:
                changes.append(PVChange(
                    pv_name=f"{prefix}{suffix}",
                    current_value=rbv_val,
                    new_value=float(sb_val),
                ))

    def _collect_offset_dependents(
        self, prefix: str, rbv: dict, spinbox: dict,
        dep_values: dict[str, float | None], changes: list[PVChange],
    ) -> None:
        delta_x = spinbox["roi_x"] - int(rbv.get("roi_x") or 0)
        delta_y = spinbox["roi_y"] - int(rbv.get("roi_y") or 0)

        if delta_x != 0:
            xform = CoordinateTransform.from_offset_change(delta_x)
            self._append_dependent_pv_changes(
                prefix, self._dependent_pvs_x, xform, dep_values, changes
            )
        if delta_y != 0:
            xform = CoordinateTransform.from_offset_change(delta_y)
            self._append_dependent_pv_changes(
                prefix, self._dependent_pvs_y, xform, dep_values, changes
            )

    def _collect_bin_dependents(
        self, prefix: str, rbv: dict, spinbox: dict,
        dep_values: dict[str, float | None], changes: list[PVChange],
    ) -> None:
        old_bin_x = rbv.get("bin_x") or 1
        new_bin_x = spinbox["bin_x"]
        old_bin_y = rbv.get("bin_y") or 1
        new_bin_y = spinbox["bin_y"]

        if int(old_bin_x) != new_bin_x:
            xform = CoordinateTransform.from_bin_change(old_bin_x, new_bin_x)
            self._append_dependent_pv_changes(
                prefix, self._dependent_pvs_size_x, xform, dep_values, changes
            )
        if int(old_bin_y) != new_bin_y:
            xform = CoordinateTransform.from_bin_change(old_bin_y, new_bin_y)
            self._append_dependent_pv_changes(
                prefix, self._dependent_pvs_size_y, xform, dep_values, changes
            )

    def _append_dependent_pv_changes(
        self,
        prefix: str,
        suffixes: list[str],
        xform: CoordinateTransform,
        dep_values: dict[str, float | None],
        changes: list[PVChange],
    ) -> None:
        for suffix in suffixes:
            pv = f"{prefix}{suffix}"
            cur = dep_values.get(pv)
            if cur is not None:
                changes.append(PVChange(
                    pv_name=pv,
                    current_value=cur,
                    new_value=xform.forward(cur),
                ))

    def _order_change_list(self, changes: list[PVChange]) -> list[PVChange]:
        """Sort changes into correct write order: bin -> size -> position -> dependent."""
        prefix = self.get_cam_prefix()
        # Priority order for direct PVs
        order_keys = [
            f"{prefix}:BinX", f"{prefix}:BinY",
            f"{prefix}:SizeX", f"{prefix}:SizeY",
            f"{prefix}:MinX", f"{prefix}:MinY",
        ]

        def sort_key(e: PVChange) -> int:
            try:
                return order_keys.index(e.pv_name)
            except ValueError:
                return len(order_keys)

        return sorted(changes, key=sort_key)

    def _after_write_sync(self):
        self._sync_spinboxes_from_hardware()
        self._exit_edit_mode()

    def _set_controls_enabled(self, enabled: bool):
        for w in (self.bin_x_spinbox, self.bin_y_spinbox,
                  self.roi_x_spinbox, self.roi_y_spinbox,
                  self.roi_width_spinbox, self.roi_height_spinbox,
                  self.sync_bins_checkbox,
                  self.reset_roi_button, self.confirm_button,
                  self.cancel_button, self.move_button, self.draw_button):
            w.setEnabled(enabled)
        self.bin_y_spinbox.setEnabled(
            enabled and not self.sync_bins_checkbox.isChecked()
        )

    # ── Reset (full sensor) ───────────────────────────────────────────────

    def _on_reset(self):
        """Set spinboxes to bin=1, full sensor and go straight to confirm."""
        sensor_w = self._rbv_value("sensor_width_label")
        sensor_h = self._rbv_value("sensor_height_label")

        self.bin_x_spinbox.blockSignals(True)
        self.bin_y_spinbox.blockSignals(True)
        self.roi_x_spinbox.blockSignals(True)
        self.roi_y_spinbox.blockSignals(True)
        self.roi_width_spinbox.blockSignals(True)
        self.roi_height_spinbox.blockSignals(True)

        self.bin_x_spinbox.setValue(1)
        self.bin_y_spinbox.setValue(1)
        self.roi_x_spinbox.setValue(0)
        self.roi_y_spinbox.setValue(0)
        if sensor_w is not None:
            self.roi_width_spinbox.setValue(int(sensor_w))
        if sensor_h is not None:
            self.roi_height_spinbox.setValue(int(sensor_h))

        self.bin_x_spinbox.blockSignals(False)
        self.bin_y_spinbox.blockSignals(False)
        self.roi_x_spinbox.blockSignals(False)
        self.roi_y_spinbox.blockSignals(False)
        self.roi_width_spinbox.blockSignals(False)
        self.roi_height_spinbox.blockSignals(False)

        # Skip edit mode — go straight to confirm
        if self._has_unsaved_changes():
            self._on_confirm()
        else:
            # Already at full sensor; nothing to do
            self._sync_spinboxes_from_hardware()

    # ── Cancel ─────────────────────────────────────────────────────────────

    def _on_cancel(self):
        """Revert spinboxes to RBV and exit edit mode."""
        self._sync_spinboxes_from_hardware()
        self._exit_edit_mode()

    # ── Edit Mode ──────────────────────────────────────────────────────────

    def _enter_edit_mode(self):
        if self._in_edit_mode:
            return
        self._in_edit_mode = True

        # Capture RBV snapshot for ROI ↔ spinbox coordinate mapping
        rbv = self._rbv_map()
        self._rbv_snapshot = {
            k: int(v) if v is not None else 0 for k, v in rbv.items()
        }

        # Show action buttons, hide trash
        self.confirm_button.setVisible(True)
        self.cancel_button.setVisible(True)
        self.reset_roi_button.setVisible(False)

        # Show ROI synced to current spinbox values
        self._sync_roi_from_spinboxes()
        self.roi_rect.setVisible(True)

    def _exit_edit_mode(self):
        if not self._in_edit_mode:
            return
        self._in_edit_mode = False
        self._draw_origin = None
        self._rbv_snapshot = {}

        # Hide ROI and action buttons, show trash
        self.roi_rect.setVisible(False)
        self.roi_rect.set_movable(False)
        self.confirm_button.setVisible(False)
        self.cancel_button.setVisible(False)
        self.reset_roi_button.setVisible(True)

        # Deselect tools
        self.move_button.setChecked(False)
        self.draw_button.setChecked(False)

    # ── ROI ↔ Spinbox Sync ─────────────────────────────────────────────────

    def _sync_roi_from_spinboxes(self):
        """Update ROI rect geometry from current spinbox values.

        ROI position is relative to the displayed image; the displayed image
        corresponds to the RBV snapshot captured on edit-mode entry.
        """
        if self._syncing_roi:
            return
        self._syncing_roi = True
        try:
            snap = self._rbv_snapshot
            roi_x = self.roi_x_spinbox.value() - snap.get("roi_x", 0)
            roi_y = self.roi_y_spinbox.value() - snap.get("roi_y", 0)
            roi_w = self.roi_width_spinbox.value()
            roi_h = self.roi_height_spinbox.value()
            if roi_w > 0 and roi_h > 0:
                self.roi_rect.set_geometry_from_corner(roi_x, roi_y, roi_w, roi_h)
        finally:
            self._syncing_roi = False

    def _on_roi_changed(self):
        """Called when ROI is moved/resized interactively — update spinboxes."""
        if self._syncing_roi:
            return
        self._syncing_roi = True
        try:
            roi_x, roi_y, roi_w, roi_h = self.roi_rect.get_geometry_wrt_corner()
            snap = self._rbv_snapshot

            new_min_x = int(round(snap.get("roi_x", 0) + roi_x))
            new_min_y = int(round(snap.get("roi_y", 0) + roi_y))
            new_w = int(round(roi_w))
            new_h = int(round(roi_h))

            for sb, val in [
                (self.roi_x_spinbox, new_min_x),
                (self.roi_y_spinbox, new_min_y),
                (self.roi_width_spinbox, new_w),
                (self.roi_height_spinbox, new_h),
            ]:
                sb.blockSignals(True)
                sb.setValue(val)
                sb.blockSignals(False)
        finally:
            self._syncing_roi = False

    # ── Tool Toggles ──────────────────────────────────────────────────────

    def _on_move_toggle(self):
        if self.move_button.isChecked():
            self.draw_button.setChecked(False)
            self._draw_origin = None
            if not self._in_edit_mode:
                self._enter_edit_mode()
            self.roi_rect.set_movable(True)
        else:
            self.roi_rect.set_movable(False)
            if not self._has_unsaved_changes():
                self._exit_edit_mode()

    def _on_draw_toggle(self):
        if self.draw_button.isChecked():
            self.move_button.setChecked(False)
            self._draw_origin = None
            self.roi_rect.set_movable(False)
            if not self._in_edit_mode:
                self._enter_edit_mode()
        else:
            self._draw_origin = None
            if not self._has_unsaved_changes():
                self._exit_edit_mode()

    # ── Scene Interaction ──────────────────────────────────────────────────

    def _on_scene_clicked(self, event):
        if not self._in_edit_mode:
            return
        if not self.draw_button.isChecked():
            return
        if event.button() != Qt.LeftButton:
            return

        scene_pos = event.scenePos()
        data_pos = self._view_box.mapSceneToView(scene_pos)

        if self._draw_origin is None:
            self._draw_origin = data_pos
            self.roi_rect.setPos(data_pos.x(), data_pos.y())
            self.roi_rect.setSize([1, 1])
        else:
            self.roi_rect.set_from_corners(self._draw_origin, data_pos)
            self._draw_origin = None
            # Sync spinboxes from the drawn rectangle
            self._on_roi_changed()
        event.accept()

    def _on_scene_moved(self, scene_pos):
        if not self._in_edit_mode:
            return
        if self._draw_origin is not None:
            data_pos = self._view_box.mapSceneToView(scene_pos)
            self.roi_rect.set_from_corners(self._draw_origin, data_pos)

    # ── Designer Properties ────────────────────────────────────────────────

    def get_dependent_pvs_x(self) -> list[str]:
        return self._dependent_pvs_x

    def set_dependent_pvs_x(self, value: list[str]) -> None:
        self._dependent_pvs_x = value if value else []

    dependent_pvs_x = pyqtProperty("QStringList", get_dependent_pvs_x, set_dependent_pvs_x)

    def get_dependent_pvs_y(self) -> list[str]:
        return self._dependent_pvs_y

    def set_dependent_pvs_y(self, value: list[str]) -> None:
        self._dependent_pvs_y = value if value else []

    dependent_pvs_y = pyqtProperty("QStringList", get_dependent_pvs_y, set_dependent_pvs_y)

    def get_dependent_pvs_size_x(self) -> list[str]:
        return self._dependent_pvs_size_x

    def set_dependent_pvs_size_x(self, value: list[str]) -> None:
        self._dependent_pvs_size_x = value if value else []

    dependent_pvs_size_x = pyqtProperty("QStringList", get_dependent_pvs_size_x, set_dependent_pvs_size_x)

    def get_dependent_pvs_size_y(self) -> list[str]:
        return self._dependent_pvs_size_y

    def set_dependent_pvs_size_y(self, value: list[str]) -> None:
        self._dependent_pvs_size_y = value if value else []

    dependent_pvs_size_y = pyqtProperty("QStringList", get_dependent_pvs_size_y, set_dependent_pvs_size_y)

    def get_crop_box_color(self) -> QColor:
        return self._crop_box_color

    def set_crop_box_color(self, color: QColor) -> None:
        self._crop_box_color = QColor(color)
        if self.roi_rect is not None:
            self.roi_rect.change_pen(color=self._crop_box_color)

    crop_box_color = pyqtProperty("QColor", get_crop_box_color, set_crop_box_color)

