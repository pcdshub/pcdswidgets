"""Managed point-of-interest marker for camera image overlays."""

import math
from enum import IntEnum

import pyqtgraph as pg
from pyqtgraph.graphicsItems.ViewBox import ViewBox
from qtpy.QtCore import Qt
from qtpy.QtGui import QColor

_ELLIPSE_SEGMENTS = 64


class MarkerStyle(IntEnum):
    """Available marker display styles."""

    CROSSHAIR_LENGTH = 0
    INFINITE_LINES = 1
    ELLIPSE = 2
    INFINITE_LINES_AND_ELLIPSE = 3


class CamMarker:
    """Composite marker overlay for a single point of interest.

    Renders on one or more pyqtgraph ViewBoxes as crosshairs of varying
    sizes, infinite (full-span) lines, an ellipse, or infinite lines
    combined with an ellipse. Wraps the graphic items so style changes
    preserve the marker position.

    A marker's (x, y) is a single absolute value; attaching it to more than
    one ViewBox renders that same value in each view's own local coordinate
    frame via a per-attachment (offset_x, offset_y).

    Parameters
    ----------
    color : QColor
        Initial pen color.
    width : int
        Initial pen width in pixels.
    style : MarkerStyle
        Initial display style.
    arm_length : int
        Initial crosshair arm length, in data coordinates. Only used when
        ``style`` is ``MarkerStyle.CROSSHAIR_LENGTH``.
    radius_x : int
        Initial ellipse radius along x, in data coordinates. Only used
        when ``style`` is ``MarkerStyle.ELLIPSE`` or
        ``MarkerStyle.INFINITE_LINES_AND_ELLIPSE``.
    radius_y : int
        Initial ellipse radius along y, in data coordinates. Only used
        when ``style`` is ``MarkerStyle.ELLIPSE`` or
        ``MarkerStyle.INFINITE_LINES_AND_ELLIPSE``.
    """

    def __init__(
        self,
        color: QColor,
        width: int = 2,
        style: MarkerStyle = MarkerStyle.CROSSHAIR_LENGTH,
        arm_length: int = 20,
        radius_x: int = 20,
        radius_y: int = 20,
        hatch_pattern: Qt.PenStyle = Qt.SolidLine,
    ):
        self._color = QColor(color)
        self._width = width
        self._style = style
        self._arm_length = arm_length
        self._radius_x = radius_x
        self._radius_y = radius_y
        self._hatch_pattern = hatch_pattern
        self._x, self._y = 0.0, 0.0
        self._visible = False

        # One entry per attached ViewBox: {"view_box", "offset_x", "offset_y", "items"}
        self._attachments: list[dict] = []

    def attach(self, view_box: ViewBox, offset: tuple[float, float] = (0.0, 0.0)) -> None:
        """Attach this marker to a pyqtgraph ViewBox, rendered at (x - offset_x, y - offset_y).

        Can be called more than once with different ViewBoxes to render the
        same marker in multiple views at once (e.g. a full-frame view with
        offset (0, 0), and a second view offset by an ROI's live MinX/MinY).
        """
        attachment = {"view_box": view_box, "offset_x": offset[0], "offset_y": offset[1], "items": []}
        self._attachments.append(attachment)
        self._rebuild_attachment(attachment)

    def set_offset(self, view_box: ViewBox, offset_x: float, offset_y: float) -> None:
        """Update the live offset for a previously-attached ViewBox (e.g. when its ROI moves)."""
        for attachment in self._attachments:
            if attachment["view_box"] is view_box:
                attachment["offset_x"] = offset_x
                attachment["offset_y"] = offset_y
                self._update_attachment_positions(attachment)
                return

    def detach(self, view_box: ViewBox | None = None) -> None:
        """Remove graphic items from one ViewBox, or every attached ViewBox if view_box is None."""
        for attachment in list(self._attachments):
            if view_box is None or attachment["view_box"] is view_box:
                self._remove_attachment_items(attachment)
                self._attachments.remove(attachment)

    def set_visible(self, visible: bool) -> None:
        self._visible = visible
        for attachment in self._attachments:
            for item in attachment["items"]:
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

    def set_radius(self, radius: int) -> None:
        """Set both radii at once, for a uniform (circular) ellipse."""
        self._radius_x = radius
        self._radius_y = radius
        self._update_positions()

    def set_radius_x(self, radius: int) -> None:
        self._radius_x = radius
        self._update_positions()

    def set_radius_y(self, radius: int) -> None:
        self._radius_y = radius
        self._update_positions()

    def set_hatch_pattern(self, pattern: Qt.PenStyle) -> None:
        self._hatch_pattern = pattern
        self._update_pens()

    @property
    def x(self) -> float:
        return self._x

    @x.setter
    def x(self, value: float):
        self._x = value
        self._update_positions()

    @property
    def y(self) -> float:
        return self._y

    @y.setter
    def y(self, value: float):
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
    def radius(self) -> int:
        """Radius along x, for callers that only care about a uniform (circular) ellipse."""
        return self._radius_x

    @property
    def radius_x(self) -> int:
        return self._radius_x

    @property
    def radius_y(self) -> int:
        return self._radius_y

    @property
    def hatch_pattern(self) -> Qt.PenStyle:
        return self._hatch_pattern

    def _rebuild(self) -> None:
        """Recreate graphic items for the current style, on every attached ViewBox."""
        for attachment in self._attachments:
            self._rebuild_attachment(attachment)

    def _rebuild_attachment(self, attachment: dict) -> None:
        """Recreate graphic items for the current style, on one attachment."""
        self._remove_attachment_items(attachment)
        view_box = attachment["view_box"]
        if view_box is None:
            return

        pen = pg.mkPen(color=self._color, width=self._width, style=self._hatch_pattern)

        if self._style == MarkerStyle.INFINITE_LINES:
            items = [pg.InfiniteLine(angle=0, pen=pen), pg.InfiniteLine(angle=90, pen=pen)]
        elif self._style == MarkerStyle.ELLIPSE:
            # A single closed polyline in data coordinates
            items = [pg.PlotDataItem(pen=pen)]
        elif self._style == MarkerStyle.INFINITE_LINES_AND_ELLIPSE:
            items = [pg.InfiniteLine(angle=0, pen=pen), pg.InfiniteLine(angle=90, pen=pen), pg.PlotDataItem(pen=pen)]
        else:
            # 4 arms radiating from center for symmetric dash patterns
            items = [pg.PlotDataItem(pen=pen) for _ in range(4)]

        try:
            for item in items:
                item.setVisible(self._visible)
                view_box.addItem(item)
        except RuntimeError:
            self._drop_attachment(attachment)
            return

        attachment["items"] = items
        self._update_attachment_positions(attachment)

    def _remove_attachment_items(self, attachment: dict) -> None:
        """Remove one attachment's current graphic items from its ViewBox."""
        view_box = attachment["view_box"]
        if view_box is not None:
            for item in attachment["items"]:
                try:
                    view_box.removeItem(item)
                except RuntimeError:
                    pass  # already gone along with the view_box/scene it lived in
        attachment["items"] = []

    def _update_positions(self) -> None:
        """Reposition items to the current center point, on every attached ViewBox."""
        for attachment in list(self._attachments):
            self._update_attachment_positions(attachment)

    def _update_attachment_positions(self, attachment: dict) -> None:
        """Reposition one attachment's items, translated by its own (offset_x, offset_y)."""
        items = attachment["items"]
        if not items:
            return

        x = self.x - attachment["offset_x"]
        y = self.y - attachment["offset_y"]

        try:
            if self._style == MarkerStyle.INFINITE_LINES:
                items[0].setValue(y)  # horizontal
                items[1].setValue(x)  # vertical
            elif self._style == MarkerStyle.ELLIPSE:
                xs, ys = self._ellipse_points(x, y)
                items[0].setData(xs, ys)
            elif self._style == MarkerStyle.INFINITE_LINES_AND_ELLIPSE:
                items[0].setValue(y)  # horizontal
                items[1].setValue(x)  # vertical
                xs, ys = self._ellipse_points(x, y)
                items[2].setData(xs, ys)
            else:
                arm = float(self._arm_length)
                # 4 arm starting from center
                items[0].setData([x, x - arm], [y, y])
                items[1].setData([x, x + arm], [y, y])
                items[2].setData([x, x], [y, y + arm])
                items[3].setData([x, x], [y, y - arm])
        except RuntimeError:
            # The ViewBox this attachment belonged to was torn down
            # elsewhere ever being called; drop it instead of raising
            # on every future position update.
            self._drop_attachment(attachment)

    def _drop_attachment(self, attachment: dict) -> None:
        if attachment in self._attachments:
            self._attachments.remove(attachment)

    def _ellipse_points(self, center_x: float, center_y: float) -> tuple[list[float], list[float]]:
        """Compute a closed polyline approximating the ellipse in data coordinates."""
        radius_x = float(self._radius_x)
        radius_y = float(self._radius_y)
        xs = []
        ys = []
        for i in range(_ELLIPSE_SEGMENTS + 1):
            theta = 2 * math.pi * i / _ELLIPSE_SEGMENTS
            xs.append(center_x + radius_x * math.cos(theta))
            ys.append(center_y + radius_y * math.sin(theta))
        return xs, ys

    def _update_pens(self) -> None:
        """Apply current pen settings to all graphic items, on every attached ViewBox."""
        pen = pg.mkPen(color=self._color, width=self._width, style=self._hatch_pattern)
        for attachment in self._attachments:
            for item in attachment["items"]:
                if isinstance(item, pg.InfiniteLine):
                    item.setPen(pen)
                elif isinstance(item, pg.PlotDataItem):
                    item.setPen(pen)
