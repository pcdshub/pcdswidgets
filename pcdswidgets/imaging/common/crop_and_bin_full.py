"""
Originally generated from jinja template ui_main_widget.j2

This file can be safely edited to change the runtime behavior of the widget.
"""

import logging

from pydm.widgets import PyDMImageView
from qtpy.QtCore import QPointF, Qt
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
        """Reset ROI to full sensor: MinX=0, MinY=0, SizeX=max, SizeY=max."""
        self.roi_x_spinbox.setValue(0)
        self.roi_x_spinbox.send_value()
        self.roi_y_spinbox.setValue(0)
        self.roi_y_spinbox.send_value()

        # Read sensor max from the readback labels if available
        sensor_w = self._get_sensor_max_x()
        sensor_h = self._get_sensor_max_y()
        if sensor_w is not None:
            self.roi_width_spinbox.setValue(sensor_w)
            self.roi_width_spinbox.send_value()
        if sensor_h is not None:
            self.roi_height_spinbox.setValue(sensor_h)
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
        if checked:
            # Immediately sync Y to X
            self.bin_y_spinbox.setValue(self.bin_x_spinbox.value)
            self.bin_y_spinbox.send_value()

    def _on_bin_x_changed(self, value):
        if self.sync_bins_checkbox.isChecked():
            self.bin_y_spinbox.setValue(value)
            self.bin_y_spinbox.send_value()

    def _on_bin_y_changed(self, value):
        if self.sync_bins_checkbox.isChecked():
            self.bin_x_spinbox.setValue(value)
            self.bin_x_spinbox.send_value()

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
            self.bin_y_spinbox,
            self.roi_x_spinbox,
            self.roi_y_spinbox,
            self.roi_width_spinbox,
            self.roi_height_spinbox,
            self.sync_bins_checkbox,
        ):
            widget.setEnabled(enabled)
        for widget in (
            self.crop_button,
            self.reset_roi_button,
        ):
            widget.setVisible(enabled)

    def _set_roi_to_full_image(self):
        """Set the ROI rect to cover the entire currently-displayed image."""
        # Current displayed image size = SizeX/BinX, SizeY/BinY
        bin_x = max(self.bin_x_spinbox.value or 1, 1)
        bin_y = max(self.bin_y_spinbox.value or 1, 1)
        size_x = self.roi_width_spinbox.value or 0
        size_y = self.roi_height_spinbox.value or 0

        display_w = size_x / bin_x
        display_h = size_y / bin_y

        if display_w > 0 and display_h > 0:
            self.roi_rect.set_geometry_from_corner(0, 0, display_w, display_h)
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
        """Compute final ROI accounting for current crop+bin, write to PVs."""
        drawn_x, drawn_y, drawn_w, drawn_h = self.roi_rect.get_geometry_wrt_corner()

        # Current state (values that are currently applied to the hardware)
        bin_x = max(self.bin_x_spinbox.value or 1, 1)
        bin_y = max(self.bin_y_spinbox.value or 1, 1)
        old_min_x = self.roi_x_spinbox.value or 0
        old_min_y = self.roi_y_spinbox.value or 0

        # Transform drawn pixels back to sensor coordinates
        new_min_x = old_min_x + (drawn_x * bin_x)
        new_min_y = old_min_y + (drawn_y * bin_y)
        new_size_x = drawn_w * bin_x
        new_size_y = drawn_h * bin_y

        # Ensure integer values
        new_min_x = int(round(new_min_x))
        new_min_y = int(round(new_min_y))
        new_size_x = int(round(new_size_x))
        new_size_y = int(round(new_size_y))

        # Exit crop mode first (re-enables spinboxes for writing)
        self._exit_crop_mode()

        # Write new values to PVs
        self.roi_x_spinbox.setValue(new_min_x)
        self.roi_x_spinbox.send_value()
        self.roi_y_spinbox.setValue(new_min_y)
        self.roi_y_spinbox.send_value()
        self.roi_width_spinbox.setValue(new_size_x)
        self.roi_width_spinbox.send_value()
        self.roi_height_spinbox.setValue(new_size_y)
        self.roi_height_spinbox.send_value()

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

