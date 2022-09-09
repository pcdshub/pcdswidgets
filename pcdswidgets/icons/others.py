from qtpy.QtCore import QPointF
from qtpy.QtGui import QPainterPath

from .base import BaseSymbolIcon


class RGASymbolIcon(BaseSymbolIcon):
    """
    A widget with a residual gas analyzer symbol drawn in it.

    Parameters
    ----------
    parent : QWidget
        The parent widget for the icon
    """
    path = QPainterPath(QPointF(0, 0))
    path.lineTo(1, 0)
    path.lineTo(1, 0.33)
    path.lineTo(0.33, 0.33)
    path.lineTo(0.33, 0.66)
    path.lineTo(0.33, 0.66)
    path.lineTo(1, 0.66)
    path.lineTo(1, 1)
    path.lineTo(0, 1)
    path.closeSubpath()

    def draw_icon(self, painter):
        painter.drawPath(self.path)
