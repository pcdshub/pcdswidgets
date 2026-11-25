"""
Colours and drawing of the ``common.ethercat`` widgets.

:data:`PALETTE` is the only place the colours are defined: the Qt colours below, the
painted icons and the ``ecatStatus`` stylesheet (a template filled in from it) all
use it. Colours follow high-performance HMI practice: neutral for normal, colour
only for meaning (Carbon support-error red for faults, Blue 60 for EDITABLE).
"""

from __future__ import annotations

from pathlib import Path
from string import Template

from qtpy import QtCore, QtGui
from qtpy.QtCore import Qt

from pcdswidgets.common.ethercat.model import H_FAULT, H_OK

PALETTE = {
    "fault": "#da1e28",  # Carbon support-error
    "editable": "#0f62fe",  # Carbon Blue 60, the interaction accent
    "muted": "#8d8d8d",  # Carbon Gray 50: OK markers and muted text, light and dark themes
    "locked": "#6f6f6f",  # Carbon Gray 60
    "unknown": "#c6c6c6",  # Carbon Gray 30
}
FAULT_RED = QtGui.QColor(PALETTE["fault"])
MUTED_GREY = QtGui.QColor(PALETTE["muted"])
LOCK_COLORS = {
    "EDITABLE": QtGui.QColor(PALETTE["editable"]),
    "LOCKED": QtGui.QColor(PALETTE["locked"]),
    "UNKNOWN": QtGui.QColor(PALETTE["unknown"]),
}

STATUS_QSS = Path(__file__).resolve().parent / "ethercat_status.qss"


def status_stylesheet() -> str:
    """The ``ecatStatus`` property rules (not a theme), with the :data:`PALETTE` colours filled in."""
    try:
        return Template(STATUS_QSS.read_text(encoding="utf-8")).substitute(PALETTE)
    except OSError:
        return ""


def set_status(widget, status: str):
    """Tag a label with ``ecatStatus`` (fault / editable / muted / ""); the status sheet colours it."""
    if widget.property("ecatStatus") == status:
        return
    widget.setProperty("ecatStatus", status)
    widget.style().unpolish(widget)
    widget.style().polish(widget)


def _icon_painter(size: int) -> tuple[QtGui.QPixmap, QtGui.QPainter]:
    """A transparent ``size`` x ``size`` pixmap and an antialiased painter on it (call ``end()``)."""
    pixmap = QtGui.QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QtGui.QPainter(pixmap)
    painter.setRenderHint(QtGui.QPainter.Antialiasing)
    return pixmap, painter


def dot_pixmap(health: int, size: int) -> QtGui.QPixmap:
    """Status marker: OK = neutral grey dot, FAULT = red dot, DISCONNECTED = dashed hollow ring."""
    pixmap, painter = _icon_painter(size)
    rect = QtCore.QRectF(1.5, 1.5, size - 3, size - 3)
    if health in (H_OK, H_FAULT):
        painter.setPen(Qt.NoPen)
        painter.setBrush(MUTED_GREY if health == H_OK else FAULT_RED)
    else:
        pen = QtGui.QPen(MUTED_GREY, 1.5)
        pen.setStyle(Qt.DashLine)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
    painter.drawEllipse(rect)
    painter.end()
    return pixmap


def lock_pixmap(access: str, size: int) -> QtGui.QPixmap:
    """Padlock: open blue = EDITABLE, closed grey = LOCKED, pale = UNKNOWN."""
    color = LOCK_COLORS.get(access, LOCK_COLORS["UNKNOWN"])
    pixmap, painter = _icon_painter(size)
    painter.setPen(QtGui.QPen(color, max(1.5, size * 0.13)))
    painter.setBrush(Qt.NoBrush)
    shackle = QtCore.QRectF(size * 0.27, size * 0.06, size * 0.46, size * 0.62)
    if access == "EDITABLE":
        shackle.translate(size * 0.16, -size * 0.04)
        painter.drawArc(shackle, 0, 180 * 16)
        painter.drawLine(
            QtCore.QPointF(shackle.left(), shackle.center().y()), QtCore.QPointF(shackle.left(), size * 0.36)
        )
    else:
        painter.drawArc(shackle, 0, 180 * 16)
    painter.setPen(Qt.NoPen)
    painter.setBrush(color)
    painter.drawRoundedRect(QtCore.QRectF(size * 0.14, size * 0.42, size * 0.72, size * 0.54), size * 0.08, size * 0.08)
    painter.end()
    return pixmap
