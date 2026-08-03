"""
Originally generated from jinja template ui_main_widget.j2

This file can be safely edited to change the runtime behavior of the widget.
"""

import logging

from pydm.widgets import PyDMImageView, PyDMLabel, PyDMSpinbox
from qtpy.QtGui import QColor, QIcon, QPixmap
from qtpy.QtWidgets import QDoubleSpinBox, QPushButton

try:
    from qtpy.QtCore import pyqtProperty
except ImportError:
    from qtpy.QtCore import Property as pyqtProperty


from pcdswidgets.builder.designer_options import DesignerOptions
from pcdswidgets.generated.imaging.common.centroid_tracker_full_base import CentroidTrackerFullBase
from pcdswidgets.icons.glyphs import CAM_COG, EYE, THICKNESS
from pcdswidgets.imaging.common.cam_marker import CamMarker, MarkerStyle
from pcdswidgets.imaging.common.centroid_marker_style_dialog import CentroidMarkerStyleDialog
from pcdswidgets.imaging.common.epics_roi_full import EpicsRoiFull

logger = logging.getLogger(__name__)

# Fixed suffixes for the shared EPICS ROI plugin PVs this widget writes to.
# (roi_plugin itself is macro-configurable; see dummy_button in the .ui.)
_ROI_MINX_SUFFIX = "MinX"
_ROI_MINY_SUFFIX = "MinY"
_ROI_SIZEX_SUFFIX = "SizeX"
_ROI_SIZEY_SUFFIX = "SizeY"


class CentroidTrackerFull(CentroidTrackerFullBase):
    centroid_visibility_button: QPushButton
    centroid_color_button: QPushButton
    centroid_style_button: QPushButton
    set_roi_button: QPushButton
    roi_multiplier_spinbox: QDoubleSpinBox

    # Labels
    centroid_x_label: PyDMLabel
    centroid_y_label: PyDMLabel
    sigma_x_label: PyDMLabel
    sigma_y_label: PyDMLabel

    designer_options = DesignerOptions(
        group="ECS Imaging Common",
        is_container=False,
        icon=CAM_COG,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._set_macro_defaults()
        self._nickname = "Centroid Tracker"

        self._image_view: PyDMImageView = None
        self._view_box = None

        # Store current sigma/centroid values
        self._sigma_x = None
        self._sigma_y = None
        self._centroid_x = None
        self._centroid_y = None

        # Stats2 (fed by ROI1) reports centroid X/Y relative to ROI1's own
        # cropped sub-array, not the full camera frame the marker/ROI2 live
        # in. _roi1_min_x/_y (kept in sync with the ROI1 selector widget via
        # link_parent_widgets) get added back onto the raw Stats2 readback -
        # see _update_absolute_centroid - so self._centroid_x/_y above stay
        # in full-frame coordinates throughout the rest of this class.
        self._roi1_min_x: float = 0.0
        self._roi1_min_y: float = 0.0
        self._centroid_x_raw = None
        self._centroid_y_raw = None

        # after_set_macro fires once per macro during initial load, but the
        # value-label hooks below should only ever be wired up once.
        self._labels_connected = False

        # If True, the ellipse marker's radius_x/radius_y track the live
        # sigma readbacks; if False, they're pinned to _default_radius.
        self._use_sigma_radius = True
        self._default_radius = 5

        # Create single marker overlay for the centroid
        self._marker = CamMarker(
            "red", radius_x=self._default_radius, radius_y=self._default_radius, style=MarkerStyle.ELLIPSE
        )

        # Hidden (never laid out) spinboxes that write the centroid-derived
        # ROI out to the shared EPICS ROI plugin PVs. The actual ROI overlay
        # and its appearance controls live in EpicsRoiFull elsewhere on the
        # screen; this widget only needs to agree with it on cam_prefix/roi_plugin.
        self._roi_pv_connected = {}
        self._roi_minx_writer = self._make_roi_pv_writer("minx")
        self._roi_miny_writer = self._make_roi_pv_writer("miny")
        self._roi_sizex_writer = self._make_roi_pv_writer("sizex")
        self._roi_sizey_writer = self._make_roi_pv_writer("sizey")
        self.set_roi_button.setVisible(False)
        self._rebuild_roi_channels()

        self._init_button_icons()
        self._apply_default_color()
        self._connect_buttons()

        # Set default ROI multiplier
        self.roi_multiplier_spinbox.setValue(3.0)
        self.roi_multiplier_spinbox.setMinimum(1.0)
        self.roi_multiplier_spinbox.setMaximum(10.0)
        self.roi_multiplier_spinbox.setSingleStep(0.5)

        self.dummy_button.setVisible(False)

    def after_set_macro(self, macro_name, value):
        self._connect_value_labels()
        self._rebuild_roi_channels()

    def _set_macro_defaults(self):
        """Populate unset macros with sensible defaults for Stat."""
        default_map = {
            "roi_plugin": ":ROI1:",
            "stat_plugin": ":Stats2:",
            "suffix_centroid_x": "CentroidX_RBV",
            "suffix_centroid_y": "CentroidY_RBV",
            "suffix_sigma_x": "SigmaX_RBV",
            "suffix_sigma_y": "SigmaY_RBV",
        }
        for name, value in default_map.items():
            self._macro_values[name] = value

    def _make_roi_pv_writer(self, key: str) -> PyDMSpinbox:
        """Create a hidden PyDMSpinbox used only to write one ROI PV.

        Never added to a layout, so it's never actually shown; PyDM connects
        a channel based on the `channel` property regardless of layout/visibility.
        """
        writer = PyDMSpinbox(parent=self)
        writer.setUserMaximum(99999.00)
        writer.setVisible(False)
        self._roi_pv_connected[key] = False
        self._wrap_connection_changed(
            writer, lambda connected, key=key: self._on_roi_pv_connection_changed(key, connected)
        )
        return writer

    def _rebuild_roi_channels(self):
        """(Re)point the hidden ROI PV writers at the current cam_prefix/roi_plugin macros."""
        base = f"ca://{self.get_cam_prefix()}{self.get_roi_plugin()}"
        self._roi_minx_writer.channel = base + _ROI_MINX_SUFFIX
        self._roi_miny_writer.channel = base + _ROI_MINY_SUFFIX
        self._roi_sizex_writer.channel = base + _ROI_SIZEX_SUFFIX
        self._roi_sizey_writer.channel = base + _ROI_SIZEY_SUFFIX

    @staticmethod
    def _wrap_connection_changed(widget, callback):
        """Patch *widget* to also invoke *callback(connected)* on connection state changes.

        Same in-place-wrap approach as _wrap_value_changed, and for the same
        reason: these widgets are never shown, so there's no visible instance
        to swap out, but connection_changed is looked up fresh on self each
        time PyDM's connectionStateChanged slot fires, so patching it in place
        on the existing instance is enough.
        """
        original = widget.connection_changed

        def wrapped(connected, _original=original, _callback=callback):
            _original(connected)
            _callback(connected)

        widget.connection_changed = wrapped

    def _on_roi_pv_connection_changed(self, key: str, connected: bool):
        """Only offer the "push ROI" button once all four ROI PVs are connected."""
        self._roi_pv_connected[key] = bool(connected)
        self.set_roi_button.setVisible(all(self._roi_pv_connected.values()))

    def _init_button_icons(self):
        """Assign SVG icons to the centroid marker's visibility and style buttons."""
        icon_map = [
            (EYE, self.centroid_visibility_button),
            (THICKNESS, self.centroid_style_button),
        ]
        for path, button in icon_map:
            icon = QIcon()
            icon.addPixmap(
                QPixmap(path),
                QIcon.Normal,
                QIcon.Off,
            )
            button.setIcon(icon)

    def _apply_default_color(self):
        """Sync color button with the marker default color."""
        self.centroid_color_button.set_color(self._marker.color)

    def _connect_buttons(self):
        """Wire up all button signals."""
        centroid_visibility_btn = self.centroid_visibility_button
        centroid_visibility_btn.setCheckable(True)
        centroid_visibility_btn.toggled.connect(self._on_visibility_toggled)

        centroid_color_btn = self.centroid_color_button
        centroid_color_btn.colorChanged.connect(lambda color: self._marker.set_color(color))

        centroid_style_btn = self.centroid_style_button
        centroid_style_btn.clicked.connect(self._open_style_dialog)

        self.set_roi_button.clicked.connect(self._set_roi_from_centroid)

    def _connect_value_labels(self):
        """Hook the centroid/sigma PyDMLabels to track their live values.

        Called from after_set_macro, which fires once per macro during
        initial load; _labels_connected ensures we only wire up once.
        """
        if self._labels_connected:
            return

        self._wrap_value_changed(self.centroid_x_label, lambda value: self._on_centroid_changed(value, "x"))
        self._wrap_value_changed(self.centroid_y_label, lambda value: self._on_centroid_changed(value, "y"))
        self._wrap_value_changed(self.sigma_x_label, lambda value: self._on_sigma_changed(value, "x"))
        self._wrap_value_changed(self.sigma_y_label, lambda value: self._on_sigma_changed(value, "y"))
        self._labels_connected = True

    @staticmethod
    def _wrap_value_changed(label: PyDMLabel, callback):
        """Patch *label* to also invoke *callback* with each new value.

        PyDMLabel has no public "new value" signal to connect to, so we
        wrap its value_changed callback in place rather than swapping out
        the widget instance (which would detach it from the layout it's
        already placed in and stop it from ever updating on screen).
        """
        original = label.value_changed

        def wrapped(new_value, _original=original, _callback=callback):
            _original(new_value)
            _callback(new_value)

        label.value_changed = wrapped

    def _on_centroid_changed(self, value: float, axis: str):
        """Update marker overlay when centroid values change from EPICS.

        The raw value is relative to ROI1, not the full camera frame the
        marker is drawn on - see the comment above _roi1_min_x in __init__.
        """
        if value is None:
            return

        try:
            value = float(value)
            if axis == "x":
                self._centroid_x_raw = value
            else:
                self._centroid_y_raw = value
            self._update_absolute_centroid()

        except (ValueError, TypeError):
            logger.warning(f"Invalid centroid value received for {axis} axis: {value}")

    def _on_roi1_offset_changed(self, value: float, axis: str) -> None:
        """Track ROI1's live MinX/MinY and re-derive the absolute centroid when it moves."""
        if value is None:
            return
        try:
            value = float(value)
        except (ValueError, TypeError):
            logger.warning(f"Invalid ROI1 offset value received for {axis} axis: {value}")
            return

        if axis == "x":
            self._roi1_min_x = value
        else:
            self._roi1_min_y = value
        self._update_absolute_centroid()

    def _update_absolute_centroid(self) -> None:
        """Recompute the full-frame centroid from the last raw Stats2 readback plus the ROI1 offset."""
        if self._centroid_x_raw is not None:
            self._centroid_x = self._roi1_min_x + self._centroid_x_raw
            self._marker.x = self._centroid_x
        if self._centroid_y_raw is not None:
            self._centroid_y = self._roi1_min_y + self._centroid_y_raw
            self._marker.y = self._centroid_y

    def _on_sigma_changed(self, value: float, axis: str):
        """Store sigma values for ROI calculation and, if enabled, the marker radius."""
        if value is None:
            return

        try:
            value = float(value)
            if axis == "x":
                self._sigma_x = value
            else:
                self._sigma_y = value

            if self._use_sigma_radius:
                self._update_marker_radius_from_sigma()

        except (ValueError, TypeError):
            logger.warning(f"Invalid sigma value received for {axis} axis: {value}")

    def _update_marker_radius_from_sigma(self):
        """Sync the ellipse marker's radius to the live sigma readbacks, per axis."""
        if self._sigma_x is not None:
            self._marker.set_radius_x(self._sigma_x)
        if self._sigma_y is not None:
            self._marker.set_radius_y(self._sigma_y)

    def _set_roi_from_centroid(self):
        """Calculate a centroid ± FWHM ROI and push it to the shared EPICS ROI PVs.

        This widget doesn't draw the ROI itself — EpicsRoiFull (pointed at the
        same cam_prefix/roi_plugin) owns that. Writing straight to the PVs
        keeps the two widgets in sync without any direct coupling.
        """
        if None in (self._centroid_x, self._centroid_y, self._sigma_x, self._sigma_y):
            logger.warning("Cannot set ROI: missing centroid or sigma values")
            return

        multiplier = self.roi_multiplier_spinbox.value()

        # Calculate FWHM from sigma (FWHM ≈ 2.355 × σ for Gaussian)
        FWHM_CONVERSION = 2.355
        fwhm_x = self._sigma_x * FWHM_CONVERSION
        fwhm_y = self._sigma_y * FWHM_CONVERSION

        # ROI size = multiplier × FWHM (e.g., 3× FWHM for "beam ± 1 beam diameter")
        roi_width = multiplier * fwhm_x
        roi_height = multiplier * fwhm_y

        # Calculate ROI min (centered on centroid)
        roi_min_x = self._centroid_x - (roi_width / 2.0)
        roi_min_y = self._centroid_y - (roi_height / 2.0)

        # Ensure minimum ROI size
        MIN_ROI_SIZE = 10  # pixels
        roi_width = max(MIN_ROI_SIZE, roi_width)
        roi_height = max(MIN_ROI_SIZE, roi_height)

        for writer, value in (
            (self._roi_minx_writer, roi_min_x),
            (self._roi_miny_writer, roi_min_y),
            (self._roi_sizex_writer, roi_width),
            (self._roi_sizey_writer, roi_height),
        ):
            writer.setValue(value)
            writer.send_value()

        self._sync_epics_roi_full_buttons()

    def _sync_epics_roi_full_buttons(self):
        """Best-effort: show the ROI and drop move-mode on any matching EpicsRoiFull.

        EpicsRoiFull is fully independent of this widget - we find one only by
        searching the shared top-level window for an instance pointed at the
        same cam_prefix/roi_plugin. No-op if none is found, and there could be
        more than one, so every match is updated.
        """
        cam_prefix = self.get_cam_prefix()
        roi_plugin = self.get_roi_plugin()
        for roi_widget in self.window().findChildren(EpicsRoiFull):
            if roi_widget.get_cam_prefix() != cam_prefix or roi_widget.get_roi_plugin() != roi_plugin:
                continue
            roi_widget.visibility_button.setChecked(True)
            roi_widget.move_enabled_button.setChecked(False)

    def link_parent_widgets(self, parent) -> None:
        """Connect this marker widget to a parent's PyDMImageView.

        Called by the parent widget at adoption time. Attaches marker
        overlay item to the ViewBox, and - if the parent also carries a
        `stats_roi_widget` (the EpicsRoiFull selecting ROI1 elsewhere on
        screen) - tracks its live MinX/MinY as the ROI1 offset needed to
        translate Stats2's centroid readback into full-frame coordinates.
        """
        if hasattr(parent, "image_view"):
            self._image_view = parent.image_view
        else:
            return

        try:
            plot_item = self._image_view.getView()
            self._view_box = plot_item.getViewBox()
        except Exception:
            logger.error("Could not get ViewBox for centroid overlays")
            return

        self._marker.attach(self._view_box)
        self._link_roi1_offset(getattr(parent, "stats_roi_widget", None))

    def _link_roi1_offset(self, stats_roi_widget) -> None:
        """Seed and live-track the ROI1 offset from the ROI1 selector's spinboxes, if given."""
        if stats_roi_widget is None:
            return
        self._roi1_min_x = stats_roi_widget.x_spinbox.value
        self._roi1_min_y = stats_roi_widget.y_spinbox.value
        stats_roi_widget.x_spinbox.valueChanged.connect(lambda v: self._on_roi1_offset_changed(v, "x"))
        stats_roi_widget.y_spinbox.valueChanged.connect(lambda v: self._on_roi1_offset_changed(v, "y"))

    def _on_visibility_toggled(self, checked: bool):
        """Toggle marker overlay visibility."""
        self._marker.set_visible(checked)

    def _open_style_dialog(self):
        """Open the style/thickness dialog for the marker."""
        marker = self._marker
        dlg = CentroidMarkerStyleDialog(
            current_style=marker.style,
            current_width=marker.width,
            current_hatch_pattern=marker.hatch_pattern,
            current_use_sigma_radius=self._use_sigma_radius,
            current_default_radius=self._default_radius,
            parent=self,
        )
        if dlg.exec_() == CentroidMarkerStyleDialog.Accepted:
            marker.set_style(dlg.selected_style)
            marker.set_width(dlg.selected_width)
            marker.set_hatch_pattern(dlg.selected_hatch_pattern)

            self._use_sigma_radius = dlg.use_sigma_radius
            self._default_radius = dlg.selected_default_radius

            if self._use_sigma_radius:
                self._update_marker_radius_from_sigma()
            else:
                marker.set_radius(self._default_radius)

    def _get_marker_color(self) -> QColor:
        return self._marker.color

    def _set_marker_color(self, color: QColor) -> None:
        self._marker.set_color(color)
        self.centroid_color_button.set_color(color)

    ## Property for marker color that can be overwritten in designer.

    def get_marker_color(self) -> QColor:
        return self._get_marker_color()

    def set_marker_color(self, color: QColor) -> None:
        self._set_marker_color(color)

    marker_color = pyqtProperty(QColor, get_marker_color, set_marker_color)

    def get_nickname(self) -> str:
        return self._nickname

    def set_nickname(self, value: str) -> None:
        self._nickname = value

    nickname = pyqtProperty(str, get_nickname, set_nickname)
