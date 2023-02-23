import math

from qtpy.QtCore import Property, QPointF, QRectF
from qtpy.QtGui import QBrush, QColor, QPainterPath, QPolygonF, QTransform

from .base import BaseSymbolIcon


class ScrollPumpSymbolIcon(BaseSymbolIcon):
    """
    A widget with a scroll pump symbol drawn in it.

    Parameters
    ----------
    parent : QWidget
        The parent widget for the icon
    """
    def __init__(self, parent=None, **kwargs):
        super().__init__(parent, **kwargs)
        self._center_brush = QBrush(QColor("transparent"))

    @Property(QBrush)
    def centerBrush(self):
        return self._center_brush

    @centerBrush.setter
    def centerBrush(self, new_brush):
        if new_brush != self._center_brush:
            self._center_brush = new_brush
            self.update()

    def draw_icon(self, painter):
        painter.drawEllipse(QPointF(0.5, 0.5), 0.5, 0.5)
        painter.drawChord(QRectF(0.0, 0.0, 1.0, 1.0), 45 * 16, -120 * 16)
        painter.drawChord(QRectF(0.0, 0.0, 1.0, 1.0), 135 * 16, 120 * 16)
        circle_arrow_point = QPointF(0.3, 0.5)

        brush = painter.brush()
        pen = painter.pen()

        painter.setBrush(self.centerBrush)
        painter.setPen(QColor("transparent"))
        painter.drawEllipse(QPointF(0.5, 0.5), 0.2, 0.2)

        painter.setBrush(brush)
        painter.setPen(pen)

        painter.drawArc(QRectF(0.3, 0.3, 0.4, 0.4), 90 * 16, -270 * 16)

        arrow = QPolygonF(
            [QPointF(-0.025, 0.0), QPointF(0.025, 0.0), QPointF(0.0, -0.025)])
        painter.setBrush(QBrush(QColor(0, 0, 0)))
        painter.drawPolygon(arrow.translated(circle_arrow_point))


class IonPumpSymbolIcon(BaseSymbolIcon):
    """
    A widget with an ion pump symbol drawn in it.

    Parameters
    ----------
    parent : QWidget
        The parent widget for the icon
    """

    def draw_icon(self, painter):
        painter.drawEllipse(QPointF(0.5, 0.5), 0.5, 0.5)
        painter.drawChord(QRectF(0.0, 0.0, 1.0, 1.0), 45 * 16, -120 * 16)
        painter.drawChord(QRectF(0.0, 0.0, 1.0, 1.0), 135 * 16, 120 * 16)
        bottom_arrow_point = QPointF(0.5, 0.8)
        painter.drawLine(bottom_arrow_point, QPointF(0.5, 0.7))
        curve_start = QPointF(0.5, 0.7)
        bend_angle = 25
        curve_end_l = QPointF(
            0.4 * math.cos(math.radians(90 + bend_angle)) + 0.5,
            -0.4 * math.sin(math.radians(90 + bend_angle)) + 0.5)
        c1 = QPointF(0.5, 0.4)
        path = QPainterPath(curve_start)
        path.quadTo(c1, curve_end_l)
        painter.drawPath(path)
        curve_end_r = QPointF(
            0.4 * math.cos(math.radians(90 - bend_angle)) + 0.5,
            -0.4 * math.sin(math.radians(90 - bend_angle)) + 0.5)
        path = QPainterPath(curve_start)
        path.quadTo(c1, curve_end_r)
        painter.drawPath(path)
        # Draw the arrow end-caps
        painter.setBrush(QBrush(QColor(0, 0, 0)))
        arrow = QPolygonF(
            [QPointF(-0.025, 0.0), QPointF(0.025, 0.0), QPointF(0.0, 0.025)])
        painter.drawPolygon(arrow.translated(bottom_arrow_point))
        t = QTransform()
        t.rotate(180.0 - 25.0)
        arrow_l = t.map(arrow)
        arrow_l = arrow_l.translated(curve_end_l)
        painter.drawPolygon(arrow_l)
        t = QTransform()
        t.rotate(180.0 + 25.0)
        arrow_r = t.map(arrow)
        arrow_r = arrow_r.translated(curve_end_r)
        painter.drawPolygon(arrow_r)


class TurboPumpSymbolIcon(BaseSymbolIcon):
    """
    A widget with a turbo pump symbol drawn in it.

    Parameters
    ----------
    parent : QWidget
        The parent widget for the icon
    """
    def __init__(self, parent=None, **kwargs):
        super().__init__(parent, **kwargs)
        self._center_brush = QBrush(QColor("transparent"))

    @Property(QBrush)
    def centerBrush(self):
        return self._center_brush

    @centerBrush.setter
    def centerBrush(self, new_brush):
        if new_brush != self._center_brush:
            self._center_brush = new_brush
            self.update()

    def draw_icon(self, painter):
        # Outer circle
        painter.drawEllipse(QPointF(0.5, 0.5), 0.5, 0.5)

        brush = painter.brush()
        pen = painter.pen()

        painter.setBrush(self.centerBrush)

        # Inner concentric circles
        painter.drawEllipse(QPointF(0.5, 0.5), 0.2, 0.2)
        painter.drawEllipse(QPointF(0.5, 0.5), 0.1, 0.1)

        painter.setBrush(brush)
        painter.setPen(pen)

        # Inner straight lines
        painter.drawChord(QRectF(0.0, 0.0, 1.0, 1.0), 45 * 16, -120 * 16)
        painter.drawChord(QRectF(0.0, 0.0, 1.0, 1.0), 135 * 16, 120 * 16)


class GetterPumpSymbolIcon(BaseSymbolIcon):
    """
    A widget with a getter pump symbol drawn in it.

    Parameters
    ----------
    parent : QWidget
        The parent widget for the icon
    """

    def draw_icon(self, painter):
        painter.drawEllipse(QPointF(0.5, 0.5), 0.5, 0.5)
        painter.drawChord(QRectF(0.0, 0.0, 1.0, 1.0), 90 * 16, -100 * 16)
        painter.drawChord(QRectF(0.0, 0.0, 1.0, 1.0), 135 * 16, 100 * 16)

        # Draw the arrow end-caps
        painter.setBrush(QBrush(QColor(0, 0, 0)))

        top_arrow_point = QPointF(0.35, 0.15)
        arrow = QPolygonF(
            [QPointF(-0.08, 0.0),
             QPointF(-0.005, 0.0),
             QPointF(-0.005, 0.15),
             QPointF(0.005, 0.15),
             QPointF(0.005, 0.0),
             QPointF(0.08, 0.0),
             QPointF(0.00, -0.08)]
        )

        t = QTransform()
        t.rotate(-25)
        top_arrow_r = t.map(arrow)
        arrow_l = top_arrow_r.translated(top_arrow_point)
        painter.drawPolygon(arrow_l)

        bottom_left_arrow_point = QPointF(0.35, 0.89)
        t = QTransform()
        t.rotate(180.0 + 25.0)
        arrow_r = t.map(arrow)
        arrow_r = arrow_r.translated(bottom_left_arrow_point)
        painter.drawPolygon(arrow_r)

        bottom_right_arrow_point = QPointF(0.85, 0.65)
        t = QTransform()
        t.rotate(180.0 - 65.0)
        arrow_r = t.map(arrow)
        arrow_r = arrow_r.translated(bottom_right_arrow_point)
        painter.drawPolygon(arrow_r)
