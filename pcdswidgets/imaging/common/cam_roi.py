"""Managed rectangular ROI for camera image overlays."""

from __future__ import annotations

import pyqtgraph as pg
from qtpy.QtCore import QPointF, QRectF, Qt
from qtpy.QtGui import QColor


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

    def __init__(self, pos=(0, 0), size=(1, 1), **kwargs):
        super().__init__(pos, size, **kwargs)

    # ── Qt geometry overrides ────────────────────────────────────────────

    def boundingRect(self) -> QRectF:
        pw = self.currentPen.width() if self.currentPen else 1
        margin = pw / 2.0 + 1
        return QRectF(0, 0, self.state["size"][0], self.state["size"][1]).adjusted(
            -margin, -margin, margin, margin
        )

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

    def update_pen(self, color: QColor, width: int) -> None:
        """Apply a new color and width to the normal and hover pens."""
        pen = pg.mkPen(color, width=width)
        hover_pen = pg.mkPen(self._inverted_color(color), width=width)
        self.setPen(pen)
        self.hoverPen = hover_pen
        if self.mouseHovering:
            self.currentPen = hover_pen
        else:
            self.currentPen = pen
        self.prepareGeometryChange()
        self.update()

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
