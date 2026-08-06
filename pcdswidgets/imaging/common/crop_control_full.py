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
from pcdswidgets.generated.imaging.common.crop_control_full_base import CropControlFullBase
from pcdswidgets.icons.glyphs import CAM_COG, CHECK, MOVE, PEN_TOOL, TRASH, X_CIRCLE
from pcdswidgets.imaging.common.batch_pv_writer import BatchPVWriterDialog, PVChange
from pcdswidgets.imaging.common.cam_roi import CamROI

logger = logging.getLogger(__name__)

DEFAULT_CROP_BOX_COLOR = "green"

DEFAULT_DEP_X = [":ROI1:MinX", ":Over1:5:PositionX", ":Over1:6:PositionX",
                 ":Over1:7:PositionX", ":Over1:8:PositionX"]
DEFAULT_DEP_Y = [":ROI1:MinY", ":Over1:5:PositionY", ":Over1:6:PositionY",
                 ":Over1:7:PositionY", ":Over1:8:PositionY"]

DEFAULT_X_START = [":IMAGE1:ROI:MinX_RBV"]
DEFAULT_Y_START = [":IMAGE1:ROI:MinY_RBV"]
DEFAULT_BIN_X = [":IMAGE1:ROI:BinX"]
DEFAULT_BIN_Y = [":IMAGE1:ROI:BinY"]


class CropControlFull(CropControlFullBase):
    """Hardware crop (ROI) control widget with interactive overlay.

    Spinbox edits and draw/move tools enter crop edit mode; confirm writes
    MinX/MinY/SizeX/SizeY and shifts dependent position PVs.
    Cancel restores spinboxes from RBV.
    """

    designer_options = DesignerOptions(
        group="ECS Imaging Common",
        is_container=False,
        icon=CAM_COG,
    )

    reset_roi_button: QPushButton
    crop_confirm_button: QPushButton
    crop_cancel_button: QPushButton
    draw_button: QPushButton
    move_button: QPushButton

    roi_x_spinbox: QSpinBox
    roi_y_spinbox: QSpinBox
    roi_width_spinbox: QSpinBox
    roi_height_spinbox: QSpinBox

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._image_view: PyDMImageView | None = None
        self._view_box = None
        self._draw_origin: QPointF | None = None
        self._edit_mode: str | None = None

        self._dependent_pvs_x: list[str] = list(DEFAULT_DEP_X)
        self._dependent_pvs_y: list[str] = list(DEFAULT_DEP_Y)

        self._image_x_start_pvs: list[str] = list(DEFAULT_X_START)
        self._image_y_start_pvs: list[str] = list(DEFAULT_Y_START)
        self._image_bin_x_pvs: list[str] = list(DEFAULT_BIN_X)
        self._image_bin_y_pvs: list[str] = list(DEFAULT_BIN_Y)

        self._crop_box_color: QColor = QColor(DEFAULT_CROP_BOX_COLOR)
        self.roi_rect = CamROI(self._crop_box_color, 2, self)

        self._init_button_icons()
        self._connect_signals()

        self.crop_confirm_button.setVisible(False)
        self.crop_cancel_button.setVisible(False)

    # ── Properties ─────────────────────────────────────────────────────────

    @property
    def _in_edit_mode(self) -> bool:
        return self._edit_mode is not None

    # ── Setup ──────────────────────────────────────────────────────────────

    def _init_button_icons(self):
        icon_map = {
            TRASH: self.reset_roi_button,
            MOVE: self.move_button,
            PEN_TOOL: self.draw_button,
            CHECK: self.crop_confirm_button,
            X_CIRCLE: self.crop_cancel_button,
        }
        for path, button in icon_map.items():
            icon = QIcon()
            icon.addPixmap(QPixmap(path), QIcon.Normal, QIcon.Off)
            button.setIcon(icon)

    def _connect_signals(self):
        self.crop_confirm_button.clicked.connect(self._on_crop_confirm)
        self.crop_cancel_button.clicked.connect(self._on_crop_cancel)
        self.reset_roi_button.clicked.connect(self._on_reset)
        self.move_button.clicked.connect(self._on_move_toggle)
        self.draw_button.clicked.connect(self._on_draw_toggle)

        self.roi_x_spinbox.valueChanged.connect(self._on_crop_spinbox_edited)
        self.roi_y_spinbox.valueChanged.connect(self._on_crop_spinbox_edited)
        self.roi_width_spinbox.valueChanged.connect(self._on_crop_spinbox_edited)
        self.roi_height_spinbox.valueChanged.connect(self._on_crop_spinbox_edited)

        self.roi_rect.sigRegionChanged.connect(self._on_roi_changed)

    def link_parent_widgets(self, parent) -> None:
        """Attach ROI overlay to parent's PyDMImageView ViewBox."""
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
        """Sync spinboxes and build coordinate transforms once cam_prefix is set."""
        if macro_name == "cam_prefix" and value:
            self._sync_spinboxes_from_hardware()
            self.roi_rect.build_transforms(
                value,
                offset_x_suffixes=self._image_x_start_pvs,
                scale_x_suffixes=self._image_bin_x_pvs,
                offset_y_suffixes=self._image_y_start_pvs,
                scale_y_suffixes=self._image_bin_y_pvs,
            )

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
            "roi_x": self._rbv_value("roi_x_rbv_label"),
            "roi_y": self._rbv_value("roi_y_rbv_label"),
            "roi_width": self._rbv_value("roi_width_rbv_label"),
            "roi_height": self._rbv_value("roi_height_rbv_label"),
        }

    def _spinbox_map(self) -> dict[str, QSpinBox]:
        return {
            "roi_x": self.roi_x_spinbox,
            "roi_y": self.roi_y_spinbox,
            "roi_width": self.roi_width_spinbox,
            "roi_height": self.roi_height_spinbox,
        }

    def _sync_spinboxes_from_hardware(self):
        rbv = self._rbv_map()
        for key, spinbox in self._spinbox_map().items():
            val = rbv.get(key)
            if val is not None:
                spinbox.blockSignals(True)
                spinbox.setValue(int(val))
                spinbox.blockSignals(False)

    def _has_unsaved_changes(self) -> bool:
        rbv = self._rbv_map()
        for key, spinbox in self._spinbox_map().items():
            val = rbv.get(key)
            if val is not None and int(val) != spinbox.value():
                return True
        return False

    # ── Spinbox callbacks ──────────────────────────────────────────────────

    def _on_crop_spinbox_edited(self, _value=None):
        if self._edit_mode == "crop":
            self._sync_roi_from_spinboxes()
        elif not self._in_edit_mode:
            self._enter_crop_edit_mode()

    # ── Edit mode ──────────────────────────────────────────────────────────

    def _enter_crop_edit_mode(self):
        self._edit_mode = "crop"
        self.crop_confirm_button.setVisible(True)
        self.crop_cancel_button.setVisible(True)
        self._sync_roi_from_spinboxes()
        self.roi_rect.setVisible(True)

    def _exit_edit_mode(self):
        if not self._in_edit_mode:
            return
        self._edit_mode = None
        self._draw_origin = None
        self.roi_rect.setVisible(False)
        self.roi_rect.set_movable(False)
        self.crop_confirm_button.setVisible(False)
        self.crop_cancel_button.setVisible(False)
        self.move_button.setChecked(False)
        self.draw_button.setChecked(False)

    # ── Confirm / cancel ───────────────────────────────────────────────────

    def _on_crop_confirm(self):
        if not self.get_cam_prefix():
            return
        self._show_confirm_dialog()

    def _on_crop_cancel(self):
        rbv = self._rbv_map()
        for key in ("roi_x", "roi_y", "roi_width", "roi_height"):
            val = rbv.get(key)
            if val is not None:
                sb = self._spinbox_map()[key]
                sb.blockSignals(True)
                sb.setValue(int(val))
                sb.blockSignals(False)
        self._exit_edit_mode()

    # ── Reset (full sensor) ────────────────────────────────────────────────

    def _on_reset(self):
        """Set ROI spinboxes to full sensor size and confirm."""
        sensor_w = self._rbv_value("sensor_width_label")
        sensor_h = self._rbv_value("sensor_height_label")

        for sb in (self.roi_x_spinbox, self.roi_y_spinbox,
                   self.roi_width_spinbox, self.roi_height_spinbox):
            sb.blockSignals(True)

        self.roi_x_spinbox.setValue(0)
        self.roi_y_spinbox.setValue(0)
        if sensor_w is not None:
            self.roi_width_spinbox.setValue(int(sensor_w))
        if sensor_h is not None:
            self.roi_height_spinbox.setValue(int(sensor_h))

        for sb in (self.roi_x_spinbox, self.roi_y_spinbox,
                   self.roi_width_spinbox, self.roi_height_spinbox):
            sb.blockSignals(False)

        if self._has_unsaved_changes():
            self._show_confirm_dialog()
        else:
            self._sync_spinboxes_from_hardware()

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
        self._collect_direct_crop_changes(prefix, rbv, spinbox, changes)
        self._collect_offset_dependents(prefix, rbv, spinbox, changes)
        return changes

    def _collect_direct_crop_changes(
        self, prefix: str, rbv: dict, spinbox: dict, changes: list[PVChange]
    ) -> None:
        for key, suffix in (
            ("roi_x", ":MinX"), ("roi_y", ":MinY"),
            ("roi_width", ":SizeX"), ("roi_height", ":SizeY"),
        ):
            rbv_val = rbv.get(key)
            sb_val = spinbox[key].value()
            if rbv_val is not None and int(rbv_val) != sb_val:
                changes.append(PVChange(
                    pv_name=f"{prefix}{suffix}",
                    change=float(sb_val - rbv_val),
                    is_multiply=False,
                ))

    def _collect_offset_dependents(
        self, prefix: str, rbv: dict, spinbox: dict,
        changes: list[PVChange],
    ) -> None:
        delta_x = spinbox["roi_x"].value() - int(rbv.get("roi_x") or 0)
        delta_y = spinbox["roi_y"].value() - int(rbv.get("roi_y") or 0)
        if delta_x != 0:
            self._append_dependent_pv_changes(
                prefix, self._dependent_pvs_x, float(-delta_x), False, changes
            )
        if delta_y != 0:
            self._append_dependent_pv_changes(
                prefix, self._dependent_pvs_y, float(-delta_y), False, changes
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

    # ── ROI ↔ Spinbox sync ─────────────────────────────────────────────────

    def _sync_roi_from_spinboxes(self):
        roi_x = self.roi_x_spinbox.value()
        roi_y = self.roi_y_spinbox.value()
        roi_w = self.roi_width_spinbox.value()
        roi_h = self.roi_height_spinbox.value()
        if roi_w > 0 and roi_h > 0:
            self.roi_rect.set_geometry_from_corner(roi_x, roi_y, roi_w, roi_h)

    def _on_roi_changed(self):
        """Called when ROI is moved/resized interactively — update spinboxes."""
        pos = self.roi_rect.pos()
        size = self.roi_rect.size()
        self.roi_rect.set_from_screen_pos_and_size(
            pos.x(), pos.y(), size.x(), size.y()
        )
        lx, ly, lw, lh = self.roi_rect.get_geometry_wrt_corner()
        for sb, val in [
            (self.roi_x_spinbox, int(round(lx))),
            (self.roi_y_spinbox, int(round(ly))),
            (self.roi_width_spinbox, int(round(lw))),
            (self.roi_height_spinbox, int(round(lh))),
        ]:
            sb.blockSignals(True)
            sb.setValue(val)
            sb.blockSignals(False)

    # ── Tool toggles ───────────────────────────────────────────────────────

    def _on_move_toggle(self):
        if self.move_button.isChecked():
            self.draw_button.setChecked(False)
            self._draw_origin = None
            if not self._in_edit_mode:
                self._enter_crop_edit_mode()
            self.roi_rect.set_movable(True)
        else:
            self.roi_rect.set_movable(False)

    def _on_draw_toggle(self):
        if self.draw_button.isChecked():
            self.move_button.setChecked(False)
            self._draw_origin = None
            self.roi_rect.set_movable(False)
            if not self._in_edit_mode:
                self._enter_crop_edit_mode()
        else:
            self._draw_origin = None

    # ── Scene interaction ──────────────────────────────────────────────────

    def _on_scene_clicked(self, event):
        if self._edit_mode != "crop":
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
            lx, ly, lw, lh = self.roi_rect.get_geometry_wrt_corner()
            for sb, val in [
                (self.roi_x_spinbox, int(round(lx))),
                (self.roi_y_spinbox, int(round(ly))),
                (self.roi_width_spinbox, int(round(lw))),
                (self.roi_height_spinbox, int(round(lh))),
            ]:
                sb.blockSignals(True)
                sb.setValue(val)
                sb.blockSignals(False)
        event.accept()

    def _on_scene_moved(self, scene_pos):
        if self._edit_mode != "crop":
            return
        if self._draw_origin is not None:
            data_pos = self._view_box.mapSceneToView(scene_pos)
            self.roi_rect.set_from_corners(self._draw_origin, data_pos)

    # ── Designer properties ────────────────────────────────────────────────

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

    def get_image_x_start_pvs(self) -> list[str]:
        return self._image_x_start_pvs

    def set_image_x_start_pvs(self, value: list[str]) -> None:
        self._image_x_start_pvs = value if value else []

    image_x_start_pvs = pyqtProperty("QStringList", get_image_x_start_pvs, set_image_x_start_pvs)

    def get_image_y_start_pvs(self) -> list[str]:
        return self._image_y_start_pvs

    def set_image_y_start_pvs(self, value: list[str]) -> None:
        self._image_y_start_pvs = value if value else []

    image_y_start_pvs = pyqtProperty("QStringList", get_image_y_start_pvs, set_image_y_start_pvs)

    def get_image_bin_x_pvs(self) -> list[str]:
        return self._image_bin_x_pvs

    def set_image_bin_x_pvs(self, value: list[str]) -> None:
        self._image_bin_x_pvs = value if value else []

    image_bin_x_pvs = pyqtProperty("QStringList", get_image_bin_x_pvs, set_image_bin_x_pvs)

    def get_image_bin_y_pvs(self) -> list[str]:
        return self._image_bin_y_pvs

    def set_image_bin_y_pvs(self, value: list[str]) -> None:
        self._image_bin_y_pvs = value if value else []

    image_bin_y_pvs = pyqtProperty("QStringList", get_image_bin_y_pvs, set_image_bin_y_pvs)

    def get_crop_box_color(self) -> QColor:
        return self._crop_box_color

    def set_crop_box_color(self, color: QColor) -> None:
        self._crop_box_color = QColor(color)
        if self.roi_rect is not None:
            self.roi_rect.change_pen(color=self._crop_box_color)

    crop_box_color = pyqtProperty("QColor", get_crop_box_color, set_crop_box_color)
