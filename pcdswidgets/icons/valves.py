from qtpy.QtCore import (QPointF, QRectF, Qt, Property)
from qtpy.QtGui import (QPainterPath, QBrush, QColor)

from .base import BaseSymbolIcon


class PneumaticValveSymbolIcon(BaseSymbolIcon):
    """
    A widget with a pneumatic valve symbol drawn in it.

    Parameters
    ----------
    parent : QWidget
        The parent widget for the icon
    """
    def __init__(self, parent=None, **kwargs):
        super(PneumaticValveSymbolIcon, self).__init__(parent, **kwargs)
        self._interlock_brush = QBrush(QColor(0, 255, 0), Qt.SolidPattern)

    @Property(QBrush)
    def interlockBrush(self):
        return self._interlock_brush

    @interlockBrush.setter
    def interlockBrush(self, new_brush):
        if new_brush != self._interlock_brush:
            self._interlock_brush = new_brush
            self.update()

    def draw_icon(self, painter):
        super(PneumaticValveSymbolIcon, self).draw_icon(painter)
        path = QPainterPath(QPointF(0, 0.3))
        path.lineTo(0, 0.9)
        path.lineTo(1, 0.3)
        path.lineTo(1, 0.9)
        path.closeSubpath()
        painter.drawPath(path)
        painter.drawLine(QPointF(0.5, 0.6), QPointF(0.5, 0.3))
        painter.setBrush(self._interlock_brush)
        painter.drawRect(QRectF(0.2, 0, 0.6, 0.3))


class FastShutterSymbolIcon(BaseSymbolIcon):
    """
    A widget with a fast shutter symbol drawn in it.

    Parameters
    ----------
    parent : QWidget
        The parent widget for the icon
    """

    def draw_icon(self, painter):
        super(FastShutterSymbolIcon, self).draw_icon(painter)
        start_angle = 10
        span_angle = 40
        spacing = 20

        for i in range(6):
            painter.drawPie(0, 0, 1, 1, start_angle*16, span_angle*16)
            start_angle += spacing + span_angle

        painter.drawEllipse(QPointF(0.5, 0.5), 0.2, 0.2)


class RightAngleManualValveSymbolIcon(BaseSymbolIcon):
    """
    A widget with a right angle manual valve symbol drawn in it.

    Parameters
    ----------
    parent : QWidget
        The parent widget for the icon
    """
    def draw_icon(self, painter):
        super(RightAngleManualValveSymbolIcon, self).draw_icon(painter)
        path = QPainterPath(QPointF(0, 0))
        path.lineTo(1, 1)
        path.lineTo(0.005, 1)
        path.lineTo(0.5, 0.5)
        path.lineTo(0, 0.9)
        path.closeSubpath()
        painter.drawPath(path)
        painter.drawEllipse(QPointF(0.5, 0.5), 0.05, 0.05)


class ApertureValveSymbolIcon(BaseSymbolIcon):
    """
    A widget with an aperture valve symbol drawn in it.

    Parameters
    ----------
    parent : QWidget
        The parent widget for the icon
    """
    def __init__(self, parent=None, **kwargs):
        super(ApertureValveSymbolIcon, self).__init__(parent, **kwargs)
        self._interlock_brush = QBrush(QColor(0, 255, 0), Qt.SolidPattern)

    @Property(QBrush)
    def interlockBrush(self):
        return self._interlock_brush

    @interlockBrush.setter
    def interlockBrush(self, new_brush):
        if new_brush != self._interlock_brush:
            self._interlock_brush = new_brush
            self.update()

    def draw_icon(self, painter):
        super(ApertureValveSymbolIcon, self).draw_icon(painter)
        path = QPainterPath(QPointF(0, 0.3))
        path.lineTo(0, 0.9)
        path.lineTo(1, 0.3)
        path.lineTo(1, 0.9)
        path.closeSubpath()
        painter.drawPath(path)
        painter.drawEllipse(QPointF(0.5, 0.6), 0.1, 0.1)
        painter.drawLine(QPointF(0.5, 0.5), QPointF(0.5, 0.3))
        painter.setBrush(self._interlock_brush)
        painter.drawRect(QRectF(0.2, 0, 0.6, 0.3))