"""Managed point-of-interest marker for camera image overlays."""

from __future__ import annotations

from enum import IntEnum

import pyqtgraph as pg
from qtpy.QtCore import QPointF
from qtpy.QtGui import QColor


class MarkerStyle(IntEnum):
    """Available marker display styles."""

    CROSSHAIR = 0
    CROSSHAIR_SMALL = 1
    CROSSHAIR_LARGE = 2
    INFINITE_LINES = 3


class CamMarker:
    """Composite marker overlay for a single point of interest.

    Renders on a pyqtgraph ViewBox as either crosshairs of varying sizes
    or infinite (full-span) lines.  Wraps the graphic items so style
    changes preserve the marker position.

    Parameters
    ----------
    color : QColor
        Initial pen color.
    width : int
        Initial pen width in pixels.
    style : MarkerStyle
        Initial display style.
    """

    def __init__(self, color: QColor, width: int = 2, style: MarkerStyle = MarkerStyle.CROSSHAIR):
        self._color = QColor(color)
        self._width = width
        self._style = style
        self._pos = QPointF(0, 0)
        self._visible = False
        self._view_box = None

        # Graphic items managed by this marker
        self._items: list[pg.GraphicsObject] = []

    # ── API ───────────────────────────────────────────────────────

    def attach(self, view_box) -> None:
        """Attach this marker to a pyqtgraph ViewBox."""
        self._view_box = view_box
        self._rebuild()

    def detach(self) -> None:
        """Remove all graphic items from the ViewBox."""
        self._remove_items()
        self._view_box = None

    def set_position(self, x: float, y: float) -> None:
        """Move marker center to (x, y) in data coordinates."""
        self._pos = QPointF(x, y)
        self._update_positions()

    def position(self) -> QPointF:
        return QPointF(self._pos)

    def set_visible(self, visible: bool) -> None:
        self._visible = visible
        for item in self._items:
            item.setVisible(visible)

    def is_visible(self) -> bool:
        return self._visible

    def set_color(self, color: QColor) -> None:
        self._color = QColor(color)
        self._update_pens()

    def set_width(self, width: int) -> None:
        self._width = width
        self._update_pens()

    def set_style(self, style: MarkerStyle) -> None:
        self._style = style
        self._rebuild()

    @property
    def style(self) -> MarkerStyle:
        return self._style

    @property
    def color(self) -> QColor:
        return QColor(self._color)

    @property
    def width(self) -> int:
        return self._width

    # ── Internal ─────────────────────────────────────────────────────────

    def _rebuild(self) -> None:
        """Recreate graphic items for the current style."""
        self._remove_items()
        if self._view_box is None:
            return

        pen = pg.mkPen(color=self._color, width=self._width)

        if self._style == MarkerStyle.INFINITE_LINES:
            h_line = pg.InfiniteLine(angle=0, pen=pen)
            v_line = pg.InfiniteLine(angle=90, pen=pen)
            self._items = [h_line, v_line]
        else:
            # Crosshair styles differ only in arm length
            h_line = pg.PlotDataItem(pen=pen)
            v_line = pg.PlotDataItem(pen=pen)
            self._items = [h_line, v_line]

        for item in self._items:
            item.setVisible(self._visible)
            self._view_box.addItem(item)

        self._update_positions()

    def _remove_items(self) -> None:
        """Remove all current graphic items from the ViewBox."""
        if self._view_box is None:
            return
        for item in self._items:
            self._view_box.removeItem(item)
        self._items.clear()

    def _arm_length(self) -> float:
        """Return crosshair arm length based on current style."""
        if self._style == MarkerStyle.CROSSHAIR_SMALL:
            return 10.0
        elif self._style == MarkerStyle.CROSSHAIR_LARGE:
            return 40.0
        else:
            return 20.0  # default CROSSHAIR

    def _update_positions(self) -> None:
        """Reposition items to the current center point."""
        x, y = self._pos.x(), self._pos.y()

        if not self._items:
            return

        if self._style == MarkerStyle.INFINITE_LINES:
            # InfiniteLine items
            self._items[0].setValue(y)  # horizontal
            self._items[1].setValue(x)  # vertical
        else:
            # PlotDataItem crosshair arms
            arm = self._arm_length()
            self._items[0].setData([x - arm, x + arm], [y, y])  # horizontal
            self._items[1].setData([x, x], [y - arm, y + arm])  # vertical

    def _update_pens(self) -> None:
        """Apply current pen settings to all graphic items."""
        pen = pg.mkPen(color=self._color, width=self._width)
        for item in self._items:
            if isinstance(item, pg.InfiniteLine):
                item.setPen(pen)
            elif isinstance(item, pg.PlotDataItem):
                item.setPen(pen)
