"""Managed point-of-interest marker for camera image overlays."""

from __future__ import annotations

from enum import IntEnum

import pyqtgraph as pg
from qtpy.QtCore import QPointF, Qt
from qtpy.QtGui import QColor


class MarkerStyle(IntEnum):
    """Available marker display styles."""

    CROSSHAIR_LENGTH = 0
    INFINITE_LINES = 1


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

    def __init__(
        self,
        color: QColor,
        width: int = 2,
        style: MarkerStyle = MarkerStyle.CROSSHAIR_LENGTH,
        arm_length: int = 20,
        hatch_pattern: Qt.PenStyle = Qt.SolidLine,
    ):
        self._color = QColor(color)
        self._width = width
        self._style = style
        self._arm_length = arm_length
        self._hatch_pattern = hatch_pattern
        self._x, self._y = 0.0, 0.0
        self._visible = False
        self._view_box = None

        # Graphic items managed by this marker
        self._items: list[pg.GraphicsObject] = []

    def attach(self, view_box) -> None:
        """Attach this marker to a pyqtgraph ViewBox."""
        self._view_box = view_box
        self._rebuild()

    def detach(self) -> None:
        """Remove all graphic items from the ViewBox."""
        self._remove_items()
        self._view_box = None

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

    def set_arm_length(self, length: int) -> None:
        self._arm_length = length
        self._update_positions()

    def set_hatch_pattern(self, pattern: Qt.PenStyle) -> None:
        self._hatch_pattern = pattern
        self._update_pens()

    @property
    def x(self) -> float:
        return self._x

    @x.setter
    def x(self, value:float):
        self._x = value
        self._update_positions()

    @property
    def y(self) -> float:
        return self._y

    @y.setter
    def y(self, value:float):
        self._y = value
        self._update_positions()

    @property
    def style(self) -> MarkerStyle:
        return self._style

    @property
    def color(self) -> QColor:
        return QColor(self._color)

    @property
    def width(self) -> int:
        return self._width

    @property
    def arm_length(self) -> int:
        return self._arm_length

    @property
    def hatch_pattern(self) -> Qt.PenStyle:
        return self._hatch_pattern

    def _rebuild(self) -> None:
        """Recreate graphic items for the current style."""
        self._remove_items()
        if self._view_box is None:
            return

        pen = pg.mkPen(color=self._color, width=self._width, style=self._hatch_pattern)

        if self._style == MarkerStyle.INFINITE_LINES:
            h_line = pg.InfiniteLine(angle=0, pen=pen)
            v_line = pg.InfiniteLine(angle=90, pen=pen)
            self._items = [h_line, v_line]
        else:
            # 4 arms radiating from center for symmetric dash patterns
            left = pg.PlotDataItem(pen=pen)
            right = pg.PlotDataItem(pen=pen)
            up = pg.PlotDataItem(pen=pen)
            down = pg.PlotDataItem(pen=pen)
            self._items = [left, right, up, down]

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

    def _update_positions(self) -> None:
        """Reposition items to the current center point."""
        if not self._items:
            return

        if self._style == MarkerStyle.INFINITE_LINES:
            self._items[0].setValue(self.y)  # horizontal
            self._items[1].setValue(self.x)  # vertical
        else:
            arm = float(self._arm_length)
            # 4 arm starting from center
            self._items[0].setData([self.x, self.x - arm], [self.y, self.y])
            self._items[1].setData([self.x, self.x + arm], [self.y, self.y])
            self._items[2].setData([self.x, self.x], [self.y, self.y + arm])
            self._items[3].setData([self.x, self.x], [self.y, self.y - arm])

    def _update_pens(self) -> None:
        """Apply current pen settings to all graphic items."""
        pen = pg.mkPen(color=self._color, width=self._width, style=self._hatch_pattern)
        for item in self._items:
            if isinstance(item, pg.InfiniteLine):
                item.setPen(pen)
            elif isinstance(item, pg.PlotDataItem):
                item.setPen(pen)
