from qtpy.QtCore import QPointF, QRectF
from qtpy.QtGui import QPainterPath

from .base import BaseSymbolIcon


class RoughGaugeSymbolIcon(BaseSymbolIcon):
    """
    A widget with a pirani gauge symbol drawn in it.

    Parameters
    ----------
    parent : QWidget
        The parent widget for the icon
    """

    path = QPainterPath(QPointF(0.5, 0))
    path.lineTo(1, 1)
    path.lineTo(0, 1)
    path.closeSubpath()

    def draw_icon(self, painter):
        painter.drawPath(self.path)


class CathodeGaugeSymbolIcon(BaseSymbolIcon):
    """
    A widget with a cathode gauge symbol drawn in it.

    Parameters
    ----------
    parent : QWidget
        The parent widget for the icon
    """

    def draw_icon(self, painter):
        painter.drawEllipse(QPointF(0.5, 0.5), 0.5, 0.5)


class HotCathodeGaugeSymbolIcon(CathodeGaugeSymbolIcon):
    """
    A widget with a hot cathode gauge symbol drawn in it.

    Parameters
    ----------
    parent : QWidget
        The parent widget for the icon
    """
    def draw_icon(self, painter):
        super().draw_icon(painter)
        painter.drawLine(QPointF(0.3, 0.1), QPointF(0.3, 0.9))
        painter.drawLine(QPointF(0.3, 0.5), QPointF(0.7, 0.5))
        painter.drawLine(QPointF(0.7, 0.1), QPointF(0.7, 0.9))


class ColdCathodeGaugeSymbolIcon(CathodeGaugeSymbolIcon):
    """
    A widget with a cold cathode gauge symbol drawn in it.

    Parameters
    ----------
    parent : QWidget
        The parent widget for the icon
    """
    def draw_icon(self, painter):
        super().draw_icon(painter)
        painter.drawArc(QRectF(0.25, 0.25, 0.5, 0.5), 45*16, 270*16)


class ColdCathodeComboGaugeSymbolIcon(CathodeGaugeSymbolIcon):
    """
    A widget with a cold cathode and rough gauge symbol drawn in it.

    Parameters
    ----------
    parent : QWidget
        The parent widget for the icon
    """
    path = QPainterPath(QPointF(0.5, 0))
    path.lineTo(.933, .75)
    path.lineTo(.067, .75)
    path.closeSubpath()

    def draw_icon(self, painter):
        super().draw_icon(painter)
        painter.drawPath(self.path)


class HotCathodeComboGaugeSymbolIcon(ColdCathodeComboGaugeSymbolIcon):
    """
    A widget with a hot cathode and rough gauge symbol drawn in it.

    Parameters
    ----------
    parent : QWidget
        The parent widget for the icon
    """
    def draw_icon(self, painter):
        super().draw_icon(painter)
        painter.drawLine(QPointF(0.4, 0.30), QPointF(0.4, 0.65))
        painter.drawLine(QPointF(0.4, 0.45), QPointF(0.6, 0.45))
        painter.drawLine(QPointF(0.6, 0.30), QPointF(0.6, 0.65))


class CapManometerGaugeSymbolIcon(RoughGaugeSymbolIcon):
    """
    A widget with a CMG gauge symbol drawn in it.

    Parameters
    ----------
    parent : QWidget
        The parent widget for the icon
    """

    def draw_icon(self, painter):
        super().draw_icon(painter)
        painter.drawLine(QPointF(0.35, 0.45), QPointF(0.35, 0.85))
        painter.drawLine(QPointF(0.35, 0.45), QPointF(0.5, 0.75))
        painter.drawLine(QPointF(0.65, 0.45), QPointF(0.65, 0.85))
        painter.drawLine(QPointF(0.65, 0.45), QPointF(0.5, 0.75))
