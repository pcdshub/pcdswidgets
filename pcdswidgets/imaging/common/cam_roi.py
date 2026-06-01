"""Managed rectangular ROI for camera image overlays."""

from __future__ import annotations

import pyqtgraph as pg
from qtpy.QtCore import QPointF, QRectF, Qt, Slot
from qtpy.QtGui import QColor
from qtpy.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QSpinBox, QVBoxLayout


class CamROI(pg.ROI):
    """High-level rectangular ROI for camera viewer overlays.

    Extends ``pg.ROI`` with:

    - Pen-width-aware bounding rect (prevents clipping of thick outlines).
    - No default handles (avoids stale handle artifacts on rebuild).
    - Pen and hover-pen management via ``update_pen``.
    - Movability toggling with automatic handle lifecycle.
    - Geometry accessors using center + size representation (matching
      typical EPICS area-detector ROI plugin PVs).
    """

    def __init__(self, ini_color, init_width, parent_window, **kwargs):
        super().__init__(pos=(0, 0), size=(1, 1), **kwargs)
        self.setVisible(False)
        self.setAcceptedMouseButtons(Qt.NoButton)
        self.translatable = False
        self.resizable = False
        self.change_pen(ini_color, init_width)
        self.parent_window = parent_window

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

    def get_geometry(self) -> tuple[float, float, float, float]:
        """Return current ROI as (center_x, center_y, width, height)."""
        pos = self.pos()
        size = self.size()
        cx = pos.x() + size.x() / 2.0
        cy = pos.y() + size.y() / 2.0
        return cx, cy, size.x(), size.y()

    def set_geometry(self, cx: float, cy: float, wx: float, wy: float) -> None:
        """Set ROI position/size from center coordinates and dimensions.

        Does nothing if width or height are non-positive.
        """
        if wx <= 0 or wy <= 0:
            return
        self.setPos(cx - wx / 2.0, cy - wy / 2.0)
        self.setSize([wx, wy])

    def set_from_corners(self, p1: QPointF, p2: QPointF) -> None:
        """Set ROI position/size from two opposite corner points.

        Enforces a minimum size of 1 pixel in each dimension.
        """
        x = min(p1.x(), p2.x())
        y = min(p1.y(), p2.y())
        w = max(abs(p2.x() - p1.x()), 1)
        h = max(abs(p2.y() - p1.y()), 1)
        self.setPos(x, y)
        self.setSize([w, h])

    def move_center_to(self, point: QPointF) -> None:
        """Reposition the ROI so its center is at *point*, preserving size."""
        size = self.size()
        self.setPos(point.x() - size.x() / 2.0, point.y() - size.y() / 2.0)

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
        # self.hover_pen = pg.mkPen(self._inverted_color(color), width)

        if self.mouseHovering:
            self.currentPen = self.hover_pen
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

    def set_interactive(self, allowed: bool) -> None:
        """Enable/disable mouse interaction without changing movability state."""
        if allowed:
            self.setAcceptedMouseButtons(Qt.LeftButton)
        else:
            self.setAcceptedMouseButtons(Qt.NoButton)
