from qtpy.QtCore import (QPointF)
from qtpy.QtGui import (QPainterPath)

from .base import BaseSymbolIcon


class PneumaticValveSymbolIcon(BaseSymbolIcon):
    """
    A widget with a vacuum valve symbol drawn in it.

    Parameters
    ----------
    parent : QWidget
        The parent widget for the icon
    """
    path = QPainterPath(QPointF(0, 0))
    path.lineTo(0, 1)
    path.lineTo(1, 0)
    path.lineTo(1, 1)
    path.closeSubpath()

    def draw_icon(self, painter):
        super(PneumaticValveSymbolIcon, self).draw_icon(painter)
        painter.drawPath(self.path)


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
