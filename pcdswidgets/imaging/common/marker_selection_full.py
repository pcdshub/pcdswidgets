"""
Originally generated from jinja template ui_main_widget.j2

This file can be safely edited to change the runtime behavior of the widget.
"""

import logging

from pydm.widgets import PyDMImageView, PyDMSpinbox
from qtpy.QtCore import Qt
from qtpy.QtGui import QColor, QIcon, QPixmap
from qtpy.QtWidgets import QPushButton

try:
    from qtpy.QtCore import pyqtProperty
except ImportError:
    from qtpy.QtCore import Property as pyqtProperty  # type: ignore

from pcdswidgets.builder.designer_options import DesignerOptions
from pcdswidgets.generated.imaging.common.marker_selection_full_base import MarkerSelectionFullBase
from pcdswidgets.icons.glyphs import CAM_COG, CROSSHAIR, EYE, THICKNESS
from pcdswidgets.imaging.common.cam_marker import CamMarker, MarkerStyle
from pcdswidgets.imaging.common.marker_style_dialog import MarkerStyleDialog

logger = logging.getLogger(__name__)

# Default colors per marker index (these can be overwritten in designer)
_DEFAULT_COLORS = [
    QColor("red"),
    QColor("green"),
    QColor("cyan"),
    QColor("magenta"),
]
NUM_MARKERS = 4


class MarkerSelectionFull(MarkerSelectionFullBase):
    """Interactive marker overlay widget for EPICS area-detector cameras.

    Provides click-to-place, visibility toggle, and style/thickness controls
    for up to 4 point-of-interest markers overlaid on a PyDMImageView.

    Positions are synced to EPICS via PyDMSpinboxs.
    """

    designer_options = DesignerOptions(
        group="ECS Imaging Common",
        is_container=False,
        icon=CAM_COG,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._set_macro_defaults()

        self._image_view: PyDMImageView = None
        self._view_box = None
        self._active_select_idx: int | None = None  # which marker is in select mode

        # Create marker overlays
        self._markers: list[CamMarker] = []
        for i in range(NUM_MARKERS):
            color = _DEFAULT_COLORS[i]
            marker = CamMarker(color, width=2, style=MarkerStyle.CROSSHAIR_LENGTH)
            self._markers.append(marker)

        self._init_button_icons()
        self._apply_default_colors()
        self._connect_buttons()
        self._connect_spinboxes()

    def _set_macro_defaults(self):
        """Populate unset macros with sensible defaults."""
        default_map = {}
        for i in range(NUM_MARKERS):
            default_map[f"suffix_{i + 1}x"] = f":Over1:{i + 5}:PositionX"
            default_map[f"suffix_{i + 1}y"] = f":Over1:{i + 5}:PositionY"

        for name, value in default_map.items():
            self._macro_values[name] = value

    def _init_button_icons(self):
        """Assign SVG icons to the select, visibility, and style buttons."""
        for i in range(NUM_MARKERS):
            icon_map = {
                CROSSHAIR: self._select_button(i),
                EYE: self._visibility_button(i),
                THICKNESS: self._style_button(i),
            }
            for path, button in icon_map.items():
                icon = QIcon()
                icon.addPixmap(
                    QPixmap(path),
                    QIcon.Normal,
                    QIcon.Off,
                )
                button.setIcon(icon)

    def _apply_default_colors(self):
        """Sync color buttons with the marker default colors."""
        for i in range(NUM_MARKERS):
            self._color_button(i).set_color(self._markers[i].color)

    def _connect_buttons(self):
        """Wire up all button signals."""
        for i in range(NUM_MARKERS):
            select_btn = self._select_button(i)
            select_btn.setCheckable(True)
            select_btn.toggled.connect(lambda checked, idx=i: self._on_select_toggled(idx, checked))

            vis_btn = self._visibility_button(i)
            vis_btn.setCheckable(True)
            vis_btn.toggled.connect(lambda checked, idx=i: self._on_visibility_toggled(idx, checked))

            color_btn = self._color_button(i)
            color_btn.colorChanged.connect(lambda color, idx=i: self._markers[idx].set_color(color))

            style_btn = self._style_button(i)
            style_btn.clicked.connect(lambda _checked, idx=i: self._open_style_dialog(idx))

    def _connect_spinboxes(self):
        """connect on-screen overlayed markers to the spinbox values."""
        for idx in range(NUM_MARKERS):
            for axis in ["x", "y"]:
                sb = self._spinbox(axis, idx)
                sb.valueChanged.connect(
                    lambda value, axis=axis, index=idx: self._on_spinbox_changed(value, axis, index)
                )

    ## helper functions to get control widget by marker index
    def _spinbox(self, axis: str, idx: int) -> PyDMSpinbox:
        return getattr(self, f"{axis}_spinbox_{idx + 1}")

    def _select_button(self, idx: int) -> QPushButton:
        return getattr(self, f"point_{idx + 1}_select")

    def _visibility_button(self, idx: int) -> QPushButton:
        return getattr(self, f"visibility_{idx + 1}")

    def _color_button(self, idx: int):
        return getattr(self, f"color_{idx + 1}_button")

    def _style_button(self, idx: int) -> QPushButton:
        suffix = "" if idx == 0 else f"_{idx + 1}"
        return getattr(self, f"style_select{suffix}")

    def link_parent_widgets(self, parent) -> None:
        """Connect this marker widget to a parent's PyDMImageView.

        Called by the parent widget at adoption time. Attaches marker
        overlay items to the ViewBox.
        """
        if hasattr(parent, "image_view"):
            self._image_view = parent.image_view
        else:
            return

        try:
            plot_item = self._image_view.getView()
            self._view_box = plot_item.getViewBox()
        except Exception:
            logger.error("Could not get ViewBox for marker overlays")
            return

        for marker in self._markers:
            marker.attach(self._view_box)

        # Listen for mouse clicks
        self._view_box.scene().sigMouseClicked.connect(self._on_scene_clicked)

    def _on_select_toggled(self, idx: int, checked: bool):
        """Enter or exit point-select mode for marker *idx*."""
        if checked:
            # Deactivate any other active select buttons
            for i in range(NUM_MARKERS):
                if i != idx:
                    self._select_button(i).setChecked(False)
            self._active_select_idx = idx
        else:
            if self._active_select_idx == idx:
                self._active_select_idx = None

    def _on_visibility_toggled(self, idx: int, checked: bool):
        """Toggle marker overlay visibility."""
        self._markers[idx].set_visible(checked)

    def _on_scene_clicked(self, event):
        """Handle mouse clicks on the ViewBox scene for point-select mode."""
        if self._active_select_idx is None:
            return
        if event.button() != Qt.LeftButton:
            return

        idx = self._active_select_idx
        scene_pos = event.scenePos()
        data_pos = self._view_box.mapSceneToView(scene_pos)

        x_sb = self._spinbox("x", idx)
        y_sb = self._spinbox("y", idx)
        # point to spinboxes (note this triggers set_position)
        x_sb.setValue(data_pos.x())
        y_sb.setValue(data_pos.y())
        # spinboxes to EPICS
        x_sb.send_value()
        y_sb.send_value()

        # force marker to be visible
        self._visibility_button(idx).setChecked(True)

        # finish selection
        self._select_button(idx).setChecked(False)
        event.accept()

    def _on_spinbox_changed(self, value: float, axis: str, index: int):
        """Update marker overlay when spinbox values change externally."""
        if axis == "x":
            self._markers[index].x = value
        else:
            self._markers[index].y = value

    def _open_style_dialog(self, idx: int):
        """Open the style/thickness dialog for marker *idx*."""
        marker = self._markers[idx]
        dlg = MarkerStyleDialog(
            current_style=marker.style,
            current_width=marker.width,
            current_arm_length=marker.arm_length,
            current_hatch_pattern=marker.hatch_pattern,
            parent=self,
        )
        if dlg.exec_() == MarkerStyleDialog.Accepted:
            targets = self._markers if dlg.apply_to_all else [marker]
            for m in targets:
                m.set_style(dlg.selected_style)
                m.set_width(dlg.selected_width)
                m.set_arm_length(dlg.selected_arm_length)
                m.set_hatch_pattern(dlg.selected_hatch_pattern)

    def _get_marker_color(self, idx: int) -> QColor:
        return self._markers[idx].color

    def _set_marker_color(self, idx: int, color: QColor) -> None:
        self._markers[idx].set_color(color)
        self._color_button(idx).set_color(color)

    ## Explicit properties for each marker that can be overwritten in designer.

    def get_color_1(self) -> QColor:
        return self._get_marker_color(0)

    def set_color_1(self, color: QColor) -> None:
        self._set_marker_color(0, color)

    color_1 = pyqtProperty(QColor, get_color_1, set_color_1)

    def get_color_2(self) -> QColor:
        return self._get_marker_color(1)

    def set_color_2(self, color: QColor) -> None:
        self._set_marker_color(1, color)

    color_2 = pyqtProperty(QColor, get_color_2, set_color_2)

    def get_color_3(self) -> QColor:
        return self._get_marker_color(2)

    def set_color_3(self, color: QColor) -> None:
        self._set_marker_color(2, color)

    color_3 = pyqtProperty(QColor, get_color_3, set_color_3)

    def get_color_4(self) -> QColor:
        return self._get_marker_color(3)

    def set_color_4(self, color: QColor) -> None:
        self._set_marker_color(3, color)

    color_4 = pyqtProperty(QColor, get_color_4, set_color_4)
