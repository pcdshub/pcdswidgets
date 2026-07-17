"""Managed rectangular ROI for camera image overlays."""

from __future__ import annotations

import pyqtgraph as pg
from qtpy.QtCore import QPointF, QRectF, Qt, Slot
from qtpy.QtGui import QColor
from qtpy.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QSpinBox, QVBoxLayout

from pcdswidgets.imaging.common.coordinate_transform import CoordinateTransform


class CamROI(pg.ROI):
    """High-level rectangular ROI for camera viewer overlays.

    Extends ``pg.ROI`` with:

    - Pen-width-aware bounding rect (prevents clipping of thick outlines).
    - No default dragging handles (avoids stale handle artifacts on rebuild).
    - Pen and hover-pen management via ``update_pen``.
    - Movability toggling with automatic handle lifecycle.
    - Geometry accessors using center(or startpoint) + size representation (matching
      typical EPICS PVs).
    - Optional coordinate transforms (transform_x / transform_y) that map
      between logical (sensor/spinbox) units and on-screen pixel coordinates.
      When transforms are set, geometry setters accept logical units and
      getters return logical units. If transforms are not ready (PV-backed
      but no value received yet), rendering is suppressed.
    """

    def __init__(self, ini_color, init_width, parent_window, **kwargs):
        super().__init__(pos=(0, 0), size=(1, 1), **kwargs)

        self.setVisible(False)
        self.setAcceptedMouseButtons(Qt.NoButton)
        self.translatable = False
        self.resizable = False
        self.change_pen(ini_color, init_width)
        self.parent_window = parent_window

        # Optional coordinate transforms (logical ↔ screen)
        self._transform_x: CoordinateTransform | None = None
        self._transform_y: CoordinateTransform | None = None

        # Stored logical (sensor) geometry — always in logical units
        self._logical_x: float = 0.0
        self._logical_y: float = 0.0
        self._logical_w: float = 1.0
        self._logical_h: float = 1.0

    # ── Transform management ─────────────────────────────────────────────

    @property
    def transform_x(self) -> CoordinateTransform | None:
        return self._transform_x

    @transform_x.setter
    def transform_x(self, xform: CoordinateTransform | None) -> None:
        if self._transform_x is not None:
            self._transform_x.values_changed.disconnect(self._on_transform_changed)
        self._transform_x = xform
        if xform is not None:
            xform.values_changed.connect(self._on_transform_changed)

    @property
    def transform_y(self) -> CoordinateTransform | None:
        return self._transform_y

    @transform_y.setter
    def transform_y(self, xform: CoordinateTransform | None) -> None:
        if self._transform_y is not None:
            self._transform_y.values_changed.disconnect(self._on_transform_changed)
        self._transform_y = xform
        if xform is not None:
            xform.values_changed.connect(self._on_transform_changed)

    def _on_transform_changed(self) -> None:
        """Re-render from stored logical geometry when transform PVs update."""
        self._render_from_logical()

    def _transforms_ready(self) -> bool:
        """Check if all set transforms have received their PV values."""
        if self._transform_x is not None and not self._transform_x.ready:
            return False
        if self._transform_y is not None and not self._transform_y.ready:
            return False
        return True

    def _to_screen_x(self, logical_x: float) -> float:
        if self._transform_x is not None:
            return self._transform_x.forward(logical_x)
        return logical_x

    def _to_screen_y(self, logical_y: float) -> float:
        if self._transform_y is not None:
            return self._transform_y.forward(logical_y)
        return logical_y

    def _to_logical_x(self, screen_x: float) -> float:
        if self._transform_x is not None:
            return self._transform_x.inverse(screen_x)
        return screen_x

    def _to_logical_y(self, screen_y: float) -> float:
        if self._transform_y is not None:
            return self._transform_y.inverse(screen_y)
        return screen_y

    def _scale_x(self) -> float:
        if self._transform_x is not None:
            return self._transform_x.effective_scale
        return 1.0

    def _scale_y(self) -> float:
        if self._transform_y is not None:
            return self._transform_y.effective_scale
        return 1.0

    def _render_from_logical(self) -> None:
        """Apply transforms to stored logical geometry and update rendering."""
        if not self._transforms_ready():
            return
        sx = self._to_screen_x(self._logical_x)
        sy = self._to_screen_y(self._logical_y)
        sw = self._logical_w * self._scale_x()
        sh = self._logical_h * self._scale_y()
        if sw > 0 and sh > 0:
            self.setPos(sx, sy)
            self.setSize([sw, sh])

    # ── Qt geometry overrides ────────────────────────────────────────────

    def boundingRect(self) -> QRectF:
        pw = self.currentPen.width() if self.currentPen else 1
        margin = pw / 2.0 + 1
        return QRectF(0, 0, self.state["size"][0], self.state["size"][1]).adjusted(-margin, -margin, margin, margin)

    def stateChanged(self, finish=True):
        # Invalidate old padded rect before the parent repaints.
        self.prepareGeometryChange()
        super().stateChanged(finish)

    # ── Geometry (center + size) ─────────────────────────────────────────

    def get_geometry_wrt_center(self) -> tuple[float, float, float, float]:
        """Return logical ROI as (center_x, center_y, width, height)."""
        cx = self._logical_x + self._logical_w / 2.0
        cy = self._logical_y + self._logical_h / 2.0
        return cx, cy, self._logical_w, self._logical_h

    def get_geometry_wrt_corner(self) -> tuple[float, float, float, float]:
        """Return logical ROI as (start_x, start_y, width, height)."""
        return self._logical_x, self._logical_y, self._logical_w, self._logical_h

    def set_geometry_from_center(self, cx: float, cy: float, wx: float, wy: float) -> None:
        """Set ROI from logical center coordinates and dimensions."""
        if wx <= 0 or wy <= 0:
            return
        self._logical_x = cx - wx / 2.0
        self._logical_y = cy - wy / 2.0
        self._logical_w = wx
        self._logical_h = wy
        self._render_from_logical()

    def set_geometry_from_corner(self, x_start: float, y_start: float, wx: float, wy: float) -> None:
        """Set ROI from logical starting coordinates and dimensions."""
        if wx <= 0 or wy <= 0:
            return
        self._logical_x = x_start
        self._logical_y = y_start
        self._logical_w = wx
        self._logical_h = wy
        self._render_from_logical()

    def set_from_corners(self, p1: QPointF, p2: QPointF) -> None:
        """Set ROI from two opposite corner points (in screen coordinates).

        The points are treated as on-screen positions (e.g. from mouse input)
        and are inverse-transformed to logical units before storage.
        """
        # Work in screen coords first to get the rectangle
        sx = min(p1.x(), p2.x())
        sy = min(p1.y(), p2.y())
        sw = max(abs(p2.x() - p1.x()), 1)
        sh = max(abs(p2.y() - p1.y()), 1)

        # Convert to logical
        self._logical_x = self._to_logical_x(sx)
        self._logical_y = self._to_logical_y(sy)
        scale_x = self._scale_x()
        scale_y = self._scale_y()
        self._logical_w = sw / scale_x if scale_x != 0 else sw
        self._logical_h = sh / scale_y if scale_y != 0 else sh

        # Render (already computed screen coords, but _render_from_logical
        # re-derives them for consistency)
        self._render_from_logical()

    def set_from_screen_pos_and_size(self, sx: float, sy: float, sw: float, sh: float) -> None:
        """Set ROI from raw screen coordinates (used by interactive move/resize).

        Inverse-transforms to logical units before storage.
        """
        self._logical_x = self._to_logical_x(sx)
        self._logical_y = self._to_logical_y(sy)
        scale_x = self._scale_x()
        scale_y = self._scale_y()
        self._logical_w = sw / scale_x if scale_x != 0 else sw
        self._logical_h = sh / scale_y if scale_y != 0 else sh
        # Don't re-render here — the ROI is already at the screen position
        # from the interactive move. Just store logical values.

    def move_center_to(self, point: QPointF) -> None:
        """Reposition the ROI so its center is at *point* (screen coords)."""
        size = self.size()
        self.setPos(point.x() - size.x() / 2.0, point.y() - size.y() / 2.0)
        # Update logical from new screen position
        pos = self.pos()
        self._logical_x = self._to_logical_x(pos.x())
        self._logical_y = self._to_logical_y(pos.y())
        scale_x = self._scale_x()
        scale_y = self._scale_y()
        self._logical_w = size.x() / scale_x if scale_x != 0 else size.x()
        self._logical_h = size.y() / scale_y if scale_y != 0 else size.y()

    # ── Pen management ───────────────────────────────────────────────────

    @Slot(bool)
    def visible(self, state: bool):
        self.setVisible(state)

    @Slot(QColor)
    def update_color(self, color: QColor):
        """a slot for setting the color"""
        self.change_pen(color=color)

    def change_pen(self, color=None, width=None):
        """
        Similar to setPen but with key differences

        - defaults to previous width or color if ommited
        - adds updates hoverpen too with inverted color
        - calls prepare Geometry to avoid ghosting due to size changes
        """
        if color is None:
            color = self.pen.color()
        if width is None:
            width = self.pen.width()

        self.pen = pg.mkPen(color=color, width=width)
        self.hoverPen = pg.mkPen(color=self._inverted_color(color), width=width)

        if self.mouseHovering:
            self.currentPen = self.hoverPen
        else:
            self.currentPen = self.pen

        self.prepareGeometryChange()
        self.update()

    def thickness_dialog(self):
        """Open a dialog to for user to select ROI pen thickness."""
        dlg = QDialog(self.parent_window)
        dlg.setWindowTitle("Line Thickness")
        layout = QVBoxLayout(dlg)

        row = QHBoxLayout()
        row.addWidget(QLabel("Thickness (px):"))
        spin = QSpinBox()
        spin.setRange(1, 20)
        spin.setValue(self.pen.width())
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
            pen_width = spin.value()
            self.change_pen(width=pen_width)

    @staticmethod
    def _inverted_color(color: QColor) -> QColor:
        """Return the RGB-inverted version of a color."""
        return QColor(255 - color.red(), 255 - color.green(), 255 - color.blue())

    # ── Movability ───────────────────────────────────────────────────────

    def set_movable(self, enabled: bool) -> None:
        """Toggle translatable/resizable state and manage scale handles."""
        self.translatable = enabled
        self.resizable = enabled
        if enabled:
            self.setAcceptedMouseButtons(Qt.LeftButton)
            if not self.handles:
                self.addScaleHandle([1, 1], [0, 0])
        else:
            self.setAcceptedMouseButtons(Qt.NoButton)
            while self.handles:
                self.removeHandle(0)
