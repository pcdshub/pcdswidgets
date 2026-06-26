"""
Originally generated from jinja template ui_main_widget.j2

This file can be safely edited to change the runtime behavior of the widget.
"""

import logging

from pydm.widgets import PyDMImageView
from qtpy.QtCore import QPointF, Qt, QTimer
from qtpy.QtGui import QColor, QIcon, QPixmap
from qtpy.QtWidgets import QPushButton

try:
    from qtpy.QtCore import pyqtProperty
except ImportError:
    from qtpy.QtCore import Property as pyqtProperty  # type: ignore

from pcdswidgets.builder.designer_options import DesignerOptions
from pcdswidgets.builder.icon_options import IconOptions
from pcdswidgets.generated.imaging.common.crop_and_bin_full_base import CropAndBinFullBase
from pcdswidgets.icons.glyphs import CHECK, X_CIRCLE, CROSSHAIR, MOVE, PEN_TOOL, TRASH, SCISSORS, CAM_COG
from pcdswidgets.imaging.common.cam_roi import CamROI
logger = logging.getLogger(__name__)

DEFAULT_SENSOR_MAX_X_SUFFIX = "MaxSizeX_RBV"
DEFAULT_SENSOR_MAX_Y_SUFFIX = "MaxSizeY_RBV"
CROP_BOX_COLOR = "green"

class CropAndBinFull(CropAndBinFullBase):
    """Hardware crop-and-bin control widget.

    Provides spinbox-based editing of MinX/MinY/SizeX/SizeY and BinX/BinY
    PVs, with an interactive crop mode that overlays a draggable ROI on
    the parent camera viewer.  PV writes are deferred until the user
    confirms the crop selection.
    """

    designer_options = DesignerOptions(
        group="ECS Imaging Common",
        is_container=False,
        icon=CAM_COG
    )

    crop_button: QPushButton
    reset_roi_button: QPushButton
    draw_button: QPushButton
    move_button: QPushButton
    center_button: QPushButton
    confirm_button: QPushButton
    cancel_button: QPushButton

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._sensor_max_x_suffix = DEFAULT_SENSOR_MAX_X_SUFFIX
        self._sensor_max_y_suffix = DEFAULT_SENSOR_MAX_Y_SUFFIX

        self._image_view: PyDMImageView = None
        self._view_box = None
        self._draw_origin: QPointF = None
        self._in_crop_mode = False
        self._last_bin_x: float = 1
        self._last_bin_y: float = 1
        self._bin_x_initialized = False
        self._bin_y_initialized = False

        # Cooldown timer: area detector sends take real time when changing bin size
        self._cooldown_timer = QTimer(self)
        self._cooldown_timer.setSingleShot(True)
        self._cooldown_timer.setInterval(1000)
        self._cooldown_timer.timeout.connect(self._on_cooldown_done)

        self.roi_rect = CamROI(QColor(CROP_BOX_COLOR), 2, self)

        self._init_button_icons()
        self._connect_buttons()

        self.roi_tools_row.setVisible(False)


    def _init_button_icons(self):
        icon_map = {
            SCISSORS: self.crop_button,
            TRASH: self.reset_roi_button,
            MOVE: self.move_button,
            CROSSHAIR: self.center_button,
            PEN_TOOL: self.draw_button,
            CHECK: self.confirm_button,
            X_CIRCLE: self.cancel_button,
        }
        for path, button in icon_map.items():
            icon = QIcon()
            icon.addPixmap(QPixmap(path), QIcon.Normal, QIcon.Off)
            button.setIcon(icon)

    def _connect_buttons(self):
        # main controls
        self.crop_button.clicked.connect(self._enter_crop_mode)
        self.reset_roi_button.clicked.connect(self._on_reset)

        # Bin X and Y sync
        self.sync_bins_checkbox.toggled.connect(self._on_sync_toggled)
        self.bin_x_spinbox.valueChanged.connect(self._on_bin_x_changed)
        self.bin_y_spinbox.valueChanged.connect(self._on_bin_y_changed)

        self.bin_x_spinbox.send_value_signal[float].connect(self._on_bin_x_sent)
        self.bin_y_spinbox.send_value_signal[float].connect(self._on_bin_y_sent)

        # Crop-mode tool toggles
        self.move_button.clicked.connect(self._on_move_toggle)
        self.center_button.clicked.connect(self._on_center_toggle)
        self.draw_button.clicked.connect(self._on_draw_toggle)

        # Confirm / cancel
        self.confirm_button.clicked.connect(self._on_confirm)
        self.cancel_button.clicked.connect(self._on_cancel)

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


    def _on_reset(self):
        """Reset ROI to full sensor: MinX=0, MinY=0, SizeX=max/bin, SizeY=max/bin."""
        self.roi_x_spinbox.setValue(0)
        self.roi_x_spinbox.send_value()
        self.roi_y_spinbox.setValue(0)
        self.roi_y_spinbox.send_value()

        # Read sensor max from the readback labels if available
        # Divide by current bin since PVs are in binned units
        sensor_w = self._get_sensor_max_x()
        sensor_h = self._get_sensor_max_y()
        bin_x = max(self._last_bin_x, 1)
        bin_y = max(self._last_bin_y, 1)
        if sensor_w is not None:
            self.roi_width_spinbox.setValue(int(sensor_w / bin_x))
            self.roi_width_spinbox.send_value()
        if sensor_h is not None:
            self.roi_height_spinbox.setValue(int(sensor_h / bin_y))
            self.roi_height_spinbox.send_value()

    def _get_sensor_max_x(self) -> float | None:
        """Read current sensor max X from the label widget's channel value."""
        try:
            return float(self.sensor_width_label.text())
        except (ValueError, AttributeError):
            return None

    def _get_sensor_max_y(self) -> float | None:
        """Read current sensor max Y from the label widget's channel value."""
        try:
            return float(self.sensor_height_label.text())
        except (ValueError, AttributeError):
            return None


    def _on_sync_toggled(self, checked: bool):
        self.bin_y_spinbox.setEnabled(not checked)
        if checked:
            # Immediately sync Y to X
            self.bin_y_spinbox.setValue(self.bin_x_spinbox.value)
            self.bin_y_spinbox.send_value()

    def _maybe_auto_sync(self):
        """If both bins have been read and are equal, enable sync checkbox."""
        if self._bin_x_initialized and self._bin_y_initialized:
            if self._last_bin_x == self._last_bin_y:
                self.sync_bins_checkbox.setChecked(True)

    def _start_cooldown(self, _value=None):
        """Disable controls for 2s after a PV write to let hardware apply."""
        if self._in_crop_mode:
            return
        self._set_controls_enabled(False)
        self._cooldown_timer.start()

    def _on_cooldown_done(self):
        """Re-enable controls after cooldown."""
        if not self._in_crop_mode:
            self._set_controls_enabled(True)

    def _on_bin_x_changed(self, value):
        print("check x")
        self._start_cooldown()
        if self.bin_x_spinbox.valueBeingSet and value > 0:
            self._last_bin_x = value
            if not self._bin_x_initialized:
                self._bin_x_initialized = True
                self._maybe_auto_sync()
        if self.sync_bins_checkbox.isChecked():
            self.bin_y_spinbox.setValue(value)
            self.bin_y_spinbox.send_value()

    def _on_bin_y_changed(self, value):
        print("check y")
        self._start_cooldown()
        if self.bin_y_spinbox.valueBeingSet and value > 0:
            self._last_bin_y = value
            if not self._bin_y_initialized:
                self._bin_y_initialized = True
                self._maybe_auto_sync()

    def _on_bin_x_sent(self, new_bin_x: float):
        """Rescale ROI X fields when BinX is sent, preserving physical sensor region."""
        old_bin_x = self._last_bin_x
        if new_bin_x <= 0 or old_bin_x <= 0:
            return
        if new_bin_x == old_bin_x:
            return
        ratio = old_bin_x / new_bin_x
        # Write size first to avoid exceeding max frame
        old_size_x = self.roi_width_spinbox.value or 0
        old_min_x = self.roi_x_spinbox.value or 0
        new_size_x = int(round(old_size_x * ratio))
        new_min_x = int(round(old_min_x * ratio))
        self.roi_width_spinbox.setValue(new_size_x)
        self.roi_width_spinbox.send_value()
        self.roi_x_spinbox.setValue(new_min_x)
        self.roi_x_spinbox.send_value()
        self._last_bin_x = new_bin_x

    def _on_bin_y_sent(self, new_bin_y: float):
        """Rescale ROI Y fields when BinY is sent, preserving physical sensor region."""
        old_bin_y = self._last_bin_y
        if new_bin_y <= 0 or old_bin_y <= 0:
            return
        if new_bin_y == old_bin_y:
            return
        ratio = old_bin_y / new_bin_y
        # Write size first to avoid exceeding max frame
        old_size_y = self.roi_height_spinbox.value or 0
        old_min_y = self.roi_y_spinbox.value or 0
        new_size_y = int(round(old_size_y * ratio))
        new_min_y = int(round(old_min_y * ratio))
        self.roi_height_spinbox.setValue(new_size_y)
        self.roi_height_spinbox.send_value()
        self.roi_y_spinbox.setValue(new_min_y)
        self.roi_y_spinbox.send_value()
        self._last_bin_y = new_bin_y

    def _enter_crop_mode(self):
        """Enter crop mode: freeze controls, show ROI tools, default to move."""
        self._in_crop_mode = True
        self._draw_origin = None

        # Freeze all editable controls
        self._set_controls_enabled(False)

        # Show tools row
        self.roi_tools_row.setVisible(True)

        # Set default ROI to full displayed image extent
        self._set_roi_to_full_image()

        # Default tool: move
        self.move_button.setChecked(True)
        self.center_button.setChecked(False)
        self.draw_button.setChecked(False)
        self.roi_rect.set_movable(True)
        self.roi_rect.setVisible(True)

    def _exit_crop_mode(self):
        """Exit crop mode: hide ROI, re-enable controls."""
        self._in_crop_mode = False
        self._draw_origin = None

        self.roi_rect.setVisible(False)
        self.roi_rect.set_movable(False)
        self.roi_tools_row.setVisible(False)
        self.crop_button.setChecked(False)

        self._set_controls_enabled(True)

    def _set_controls_enabled(self, enabled: bool):
        """Enable/disable or toggle visibility all spinboxes and bin controls."""
        for widget in (
            self.bin_x_spinbox,
            self.roi_x_spinbox,
            self.roi_y_spinbox,
            self.roi_width_spinbox,
            self.roi_height_spinbox,
            self.sync_bins_checkbox,
        ):
            widget.setEnabled(enabled)
        # bin_y stays disabled when sync is on
        self.bin_y_spinbox.setEnabled(
            enabled and not self.sync_bins_checkbox.isChecked()
        )
        for widget in (
            self.crop_button,
            self.reset_roi_button,
        ):
            widget.setVisible(enabled)

    def _set_roi_to_full_image(self):
        """Set the ROI rect to cover the entire currently-displayed image."""
        # SizeX/SizeY are already in binned units = displayed pixel count
        size_x = self.roi_width_spinbox.value or 0
        size_y = self.roi_height_spinbox.value or 0

        if size_x > 0 and size_y > 0:
            self.roi_rect.set_geometry_from_corner(0, 0, size_x, size_y)
        else:
            self.roi_rect.set_geometry_from_corner(0, 0, 1, 1)


    def _on_move_toggle(self):
        self.move_button.setChecked(True)
        self.center_button.setChecked(False)
        self.draw_button.setChecked(False)
        self._draw_origin = None
        self.roi_rect.set_movable(True)

    def _on_center_toggle(self):
        self.center_button.setChecked(True)
        self.move_button.setChecked(False)
        self.draw_button.setChecked(False)
        self._draw_origin = None
        self.roi_rect.set_movable(False)

    def _on_draw_toggle(self):
        self.draw_button.setChecked(True)
        self.move_button.setChecked(False)
        self.center_button.setChecked(False)
        self._draw_origin = None
        self.roi_rect.set_movable(False)

    def _on_scene_clicked(self, event):
        if not self._in_crop_mode:
            return
        if event.button() != Qt.LeftButton:
            return

        scene_pos = event.scenePos()
        data_pos = self._view_box.mapSceneToView(scene_pos)

        if self.draw_button.isChecked():
            if self._draw_origin is None:
                self._draw_origin = data_pos
                self.roi_rect.setPos(data_pos.x(), data_pos.y())
                self.roi_rect.setSize([1, 1])
            else:
                self.roi_rect.set_from_corners(self._draw_origin, data_pos)
                self._draw_origin = None
            event.accept()
        elif self.center_button.isChecked():
            self.roi_rect.move_center_to(data_pos)
            event.accept()

    def _on_scene_moved(self, scene_pos):
        if not self._in_crop_mode:
            return
        if self._draw_origin is not None:
            data_pos = self._view_box.mapSceneToView(scene_pos)
            self.roi_rect.set_from_corners(self._draw_origin, data_pos)


    def _on_confirm(self):
        """Write drawn ROI to PVs. Drawn coords are in binned-pixel units."""
        drawn_x, drawn_y, drawn_w, drawn_h = self.roi_rect.get_geometry_wrt_corner()

        # The ROI overlay is on the displayed (binned) image, so drawn
        # coordinates are already in binned units. Offset by current MinX/MinY
        # to get the new absolute position in binned coords.
        old_min_x = self.roi_x_spinbox.value or 0
        old_min_y = self.roi_y_spinbox.value or 0

        new_min_x = int(round(old_min_x + drawn_x))
        new_min_y = int(round(old_min_y + drawn_y))
        new_size_x = int(round(drawn_w))
        new_size_y = int(round(drawn_h))

        # Exit crop mode first (re-enables spinboxes for writing)
        self._exit_crop_mode()

        # Write size first, then position to avoid exceeding max
        self.roi_width_spinbox.setValue(new_size_x)
        self.roi_width_spinbox.send_value()
        self.roi_height_spinbox.setValue(new_size_y)
        self.roi_height_spinbox.send_value()
        self.roi_x_spinbox.setValue(new_min_x)
        self.roi_x_spinbox.send_value()
        self.roi_y_spinbox.setValue(new_min_y)
        self.roi_y_spinbox.send_value()

    def _on_cancel(self):
        """Discard crop selection and return to normal mode."""
        self._exit_crop_mode()

    def get_sensor_max_x_suffix(self) -> str:
        return self._sensor_max_x_suffix

    def set_sensor_max_x_suffix(self, value: str) -> None:
        self._sensor_max_x_suffix = value

    sensor_max_x_suffix = pyqtProperty(str, get_sensor_max_x_suffix, set_sensor_max_x_suffix)

    def get_sensor_max_y_suffix(self) -> str:
        return self._sensor_max_y_suffix

    def set_sensor_max_y_suffix(self, value: str) -> None:
        self._sensor_max_y_suffix = value

    sensor_max_y_suffix = pyqtProperty(str, get_sensor_max_y_suffix, set_sensor_max_y_suffix)

