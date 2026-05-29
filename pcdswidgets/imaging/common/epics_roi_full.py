"""
Originally generated from jinja template ui_main_widget.j2

This file can be safely edited to change the runtime behavior of the widget.
"""

import logging

from pydm.widgets import PyDMImageView
from qtpy.QtCore import QPointF, Qt, QTimer
from qtpy.QtGui import QColor, QIcon, QPixmap
from qtpy.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QSpinBox, QVBoxLayout

try:
    from qtpy.QtCore import pyqtProperty
except ImportError:
    from qtpy.QtCore import Property as pyqtProperty  # type: ignore

from pcdswidgets.builder.designer_options import DesignerOptions
from pcdswidgets.builder.icon_options import IconOptions
from pcdswidgets.generated.imaging.common.epics_roi_full_base import EpicsRoiFullBase
from pcdswidgets.icons.glyphs import CROSSHAIR, EYE, MOVE, PEN_TOOL, THICKNESS
from pcdswidgets.imaging.common.cam_roi import CamROI

logger = logging.getLogger(__name__)


class EpicsRoiFull(EpicsRoiFullBase):
    """Interactive ROI overlay widget for EPICS area-detector cameras.

    Provides draw, center-select, move/resize, and color/thickness controls
    for a rectangular ROI overlaid on a PyDMImageView.

    ROI geometry is synchronised with EPICS PVs via PyDMSpinbox
    channels.
    """

    draw_roi_button: QPushButton
    select_center_button: QPushButton
    visibility_button: QPushButton
    color_selection_button: QPushButton
    move_enabled_button: QPushButton
    line_thickness_button: QPushButton

    designer_options = DesignerOptions(
        group="ECS Imaging Common",
        is_container=False,
        icon=IconOptions.NONE,
    )

    # Interaction modes — mutually exclusive
    MODE_NONE = 0
    MODE_DRAW = 1
    MODE_CENTER = 2
    MODE_MOVE = 3

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._set_macro_defaults()

        self.roi_rect: CamROI | None = None
        self._image_view: PyDMImageView = None
        self._view_box = None
        self._mode = self.MODE_NONE
        self._draw_origin: QPointF = None
        self._is_visible = False
        self._pen_width = 3
        self._syncing = False

        # Debounce timer for EPICS channel updates arriving sequentially
        self._spinbox_debounce = QTimer(self)
        self._spinbox_debounce.setSingleShot(True)
        self._spinbox_debounce.setInterval(50)  # ms
        self._spinbox_debounce.timeout.connect(self._apply_spinbox_to_roi)

        self._init_button_icons()
        self._connect_buttons()

    def _set_macro_defaults(self):
        """Populate unset macros with sensible defaults for ROI1."""
        default_map = {
            "nickname": "ROI 1",
            "roi_plugin": ":ROI1:",
            "suffix_X": "MinX",
            "suffix_Y": "MinY",
            "suffix_WidthX": "SizeX",
            "suffix_WidthY": "SizeY",
        }
        for name, value in default_map.items():
            if (name not in self._macro_values) or (self._macro_values[name] == ""):
                self._macro_values[name] = value

    # The nickname macro is not auto-generated because no child widgets
    # reference it in their channel templates. We define it manually here
    # so the parent adoption code can identify this ROI by name.
    def get_nickname(self) -> str:
        return self._get_macro("nickname")

    def set_nickname(self, value: str) -> None:
        self._set_macro("nickname", value)

    nickname = pyqtProperty(str, get_nickname, set_nickname)

    def _init_button_icons(self):
        """Assign SVG icons to the toolbar buttons."""
        icon_map = {
            PEN_TOOL: self.draw_roi_button,
            CROSSHAIR: self.select_center_button,
            EYE: self.visibility_button,
            MOVE: self.move_enabled_button,
            THICKNESS: self.line_thickness_button,
        }
        for path, button in icon_map.items():
            icon = QIcon()
            icon.addPixmap(
                QPixmap(path),
                QIcon.Normal,
                QIcon.Off,
            )
            button.setIcon(icon)

    def _connect_buttons(self):
        """Wire up button click signals."""
        self.draw_roi_button.setCheckable(True)
        self.select_center_button.setCheckable(True)
        self.move_enabled_button.setCheckable(True)
        self.visibility_button.setCheckable(True)

        #mode select toggles
        self.draw_roi_button.toggled.connect(lambda new_state: self._on_mode_toggled(self.MODE_DRAW, new_state))
        self.select_center_button.toggled.connect(lambda new_state: self._on_mode_toggled(self.MODE_CENTER, new_state))
        self.move_enabled_button.toggled.connect(lambda new_state: self._on_mode_toggled(self.MODE_MOVE, new_state))
        # visibility toggle
        self.visibility_button.toggled.connect(self._on_visibility_toggled)
        # open pen edit settings
        self.color_selection_button.colorChanged.connect(self._on_color_changed)
        self.line_thickness_button.clicked.connect(self._on_thickness_clicked)

    def link_parent_widgets(self, parent) -> None:
        """
        Connect this ROI widget to a parent's PyDMImageView.

        Called by the parent widget at adoption time.  Creates the ROI
        overlay item, attaches it to the ViewBox, and wires up mouse and
        spinbox signals for bidirectional synchronisation.
        """
        if hasattr(parent, "image_view"):
            self._image_view = parent.image_view
        else:
            return
        try:
            plot_item = self._image_view.getView()
            self._view_box = plot_item.getViewBox()
        except Exception:
            logger.error("Could not get ViewBox for overlays")
            return

        self.roi_rect = CamROI(self.get_roi_color(), self._pen_width)
        self._view_box.addItem(self.roi_rect)

        # Sync ROI → spinboxes when user finishes dragging in move mode
        self.roi_rect.sigRegionChangeFinished.connect(self._on_roi_moved)

        # Listen for mouse clicks on the view for draw/center modes
        self._view_box.scene().sigMouseClicked.connect(self._on_scene_clicked)
        self._view_box.scene().sigMouseMoved.connect(self._on_scene_moved)

        # Sync ROI from EPICS channel updates (camonitor / initial read)
        for spinbox in (self.PyDMSpinbox_13, self.PyDMSpinbox_12, self.PyDMSpinbox_11, self.PyDMSpinbox_14):
            spinbox.valueChanged.connect(self._sync_roi_from_spinboxes)

    # ── Mode management ────────────────────────────────────────────────────
    #
    # Draw, center, and move are mutually exclusive interaction modes.
    # While any mode is active, inbound EPICS spinbox updates are suppressed
    # so they don't fight the user.  When an action completes (second draw
    # click, center click, or drag-finish) we push ROI → spinboxes.

    def _on_mode_toggled(self, mode: int, checked: bool) -> None:
        """Unified handler for mutually exclusive mode buttons."""
        if checked:
            self._enter_mode(mode)
        else:
            self._exit_mode(mode)

    def _enter_mode(self, mode: int) -> None:
        """Activate a mode, deactivating any other."""
        # Uncheck other mode buttons first — their toggled(False) handlers
        # see _mode == NONE and exit harmlessly.
        for m, btn in self._mode_buttons().items():
            if m != mode:
                btn.setChecked(False)
        self._mode = mode
        # Mode-specific setup
        if mode == self.MODE_MOVE and self.roi_rect:
            self.roi_rect.set_movable(True)

    def _exit_mode(self, mode: int) -> None:
        """Leave *mode* and return to idle. No-op if already in a different mode."""
        if self._mode != mode:
            return
        # Mode-specific teardown
        if mode == self.MODE_DRAW:
            self._draw_origin = None
        elif mode == self.MODE_MOVE and self.roi_rect:
            self.roi_rect.set_movable(False)
        self._mode = self.MODE_NONE

    def _mode_buttons(self) -> dict:
        """Map mode constants to their toggle buttons."""
        return {
            self.MODE_DRAW: self.draw_roi_button,
            self.MODE_CENTER: self.select_center_button,
            self.MODE_MOVE: self.move_enabled_button,
        }

    def _on_visibility_toggled(self, checked: bool):
        """Toggle ROI overlay visibility."""
        if self.roi_rect is None:
            return
        self._is_visible = checked
        self.roi_rect.setVisible(checked)

    def _on_thickness_clicked(self):
        """Open a dialog to set the ROI pen thickness."""
        dlg = QDialog(self)
        dlg.setWindowTitle("Line Thickness")
        layout = QVBoxLayout(dlg)

        row = QHBoxLayout()
        row.addWidget(QLabel("Thickness (px):"))
        spin = QSpinBox()
        spin.setRange(1, 20)
        spin.setValue(self._pen_width)
        row.addWidget(spin)
        layout.addLayout(row)

        btn_row = QHBoxLayout()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")
        btn_row.addWidget(ok_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

        ok_btn.clicked.connect(dlg.accept)
        cancel_btn.clicked.connect(dlg.reject)

        if dlg.exec_() == QDialog.Accepted:
            self._pen_width = spin.value()
            self._apply_pen()

    def _on_color_changed(self, color: QColor):
        """Update ROI pen color when user picks a new color."""
        if self.roi_rect is None:
            return
        self._apply_pen()

    # ── Scene mouse event handlers ───────────────────────────────────────

    def _on_scene_clicked(self, event):
        """Handle mouse clicks on the ViewBox scene for draw/center modes."""
        if self._mode == self.MODE_NONE or self._view_box is None:
            return

        # Only respond to left-click
        if event.button() != Qt.LeftButton:
            return

        scene_pos = event.scenePos()
        data_pos = self._view_box.mapSceneToView(scene_pos)

        if self._mode == self.MODE_DRAW:
            self._handle_draw_click(data_pos)
            event.accept()
        elif self._mode == self.MODE_CENTER:
            self._handle_centering_click(data_pos)
            event.accept()

    def _on_scene_moved(self, scene_pos):
        """Live-update ROI size while dragging during draw mode."""
        if self._mode != self.MODE_DRAW or self._draw_origin is None:
            return
        if self._view_box is None or self.roi_rect is None:
            return

        data_pos = self._view_box.mapSceneToView(scene_pos)
        self._update_roi_from_corners(self._draw_origin, data_pos)

    # ── Draw mode logic ──────────────────────────────────────────────────

    def _handle_draw_click(self, data_pos: QPointF):
        """First click sets origin, second click finalises the ROI."""
        if self._draw_origin is None:
            # First click – start drawing
            self._draw_origin = data_pos
            self._set_visible(True)
            self.roi_rect.setPos(data_pos.x(), data_pos.y())
            self.roi_rect.setSize([1, 1])
        else:
            # Second click – finalise
            self.roi_rect.set_from_corners(self._draw_origin, data_pos)
            self._sync_spinboxes_from_roi()
            self._draw_origin = None
            # Exit draw mode
            self.draw_roi_button.setChecked(False)

    def _update_roi_from_corners(self, p1: QPointF, p2: QPointF):
        """Set ROI position/size from two corner points."""
        self.roi_rect.set_from_corners(p1, p2)

    # ── Center mode logic ────────────────────────────────────────────────

    def _handle_centering_click(self, data_pos: QPointF):
        """Move ROI center to the clicked position, keep size."""
        if self.roi_rect is None:
            return
        self.roi_rect.move_center_to(data_pos)
        self._set_visible(True)
        self._sync_spinboxes_from_roi()
        # Exit center mode
        self.select_center_button.setChecked(False)

    # ── ROI ↔ Spinbox synchronisation ────────────────────────────────────

    def _on_roi_moved(self):
        """Called when user finishes dragging the ROI in move mode."""
        if self._syncing or self._mode != self.MODE_MOVE:
            return
        self._sync_spinboxes_from_roi()

    def _sync_spinboxes_from_roi(self):
        """Push ROI geometry into the PyDMSpinbox widgets (EPICS channels)."""
        if self.roi_rect is None or self._syncing:
            return
        self._syncing = True
        try:
            cx, cy, wx, wy = self.roi_rect.get_geometry()

            # PyDMSpinbox_13 = CenterX, PyDMSpinbox_12 = CenterY
            # PyDMSpinbox_11 = WidthX,  PyDMSpinbox_14 = WidthY
            for spinbox, value in (
                (self.PyDMSpinbox_13, cx),
                (self.PyDMSpinbox_12, cy),
                (self.PyDMSpinbox_11, wx),
                (self.PyDMSpinbox_14, wy),
            ):
                spinbox.setValue(value)
                spinbox.send_value_signal[float].emit(value)
        finally:
            self._syncing = False

    def _sync_roi_from_spinboxes(self, _value=None):
        """Debounce EPICS → ROI updates; suppressed while user is interacting."""
        if self._syncing or self.roi_rect is None:
            return
        if self._mode != self.MODE_NONE:
            return
        self._spinbox_debounce.start()

    def _apply_spinbox_to_roi(self):
        """Actually update ROI geometry after debounce settles."""
        if self._syncing or self.roi_rect is None:
            return
        self._syncing = True
        try:
            cx = self.PyDMSpinbox_13.value
            cy = self.PyDMSpinbox_12.value
            wx = self.PyDMSpinbox_11.value
            wy = self.PyDMSpinbox_14.value
            if None in (cx, cy, wx, wy):
                return
            self.roi_rect.set_geometry(cx, cy, wx, wy)
        finally:
            self._syncing = False

    # ── Helpers ──────────────────────────────────────────────────────────

    def _set_visible(self, visible: bool):
        """Single source of truth for ROI visibility state."""
        if self.roi_rect is None:
            return
        self._is_visible = visible
        self.roi_rect.setVisible(visible)
        self.visibility_button.setChecked(visible)

    def _apply_pen(self):
        """Apply current color and thickness to the ROI pen."""
        if self.roi_rect is None:
            return
        self.roi_rect.update_pen(self.get_roi_color(), self._pen_width)

    def get_roi_color(self) -> QColor:
        return self.color_selection_button.color

    def set_roi_color(self, color: QColor) -> None:
        self.color_selection_button.color = color

    roi_color = pyqtProperty(QColor, get_roi_color, set_roi_color)
