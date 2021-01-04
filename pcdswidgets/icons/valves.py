import math

from qtpy.QtCore import (QPointF, QRectF, Qt, Property, QLineF)
from qtpy.QtGui import (QPainterPath, QBrush, QColor, QPolygonF, QTransform)

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
    def __init__(self, parent=None, **kwargs):
        super(FastShutterSymbolIcon, self).__init__(parent, **kwargs)
        self._arrow_brush = QBrush(QColor("transparent"), Qt.SolidPattern)

    @Property(QBrush)
    def arrowBrush(self):
        return self._arrow_brush

    @arrowBrush.setter
    def arrowBrush(self, new_brush):
        if new_brush != self._arrow_brush:
            self._arrow_brush = new_brush
            self.update()

    def draw_icon(self, painter):
        path = QPainterPath(QPointF(0, 0.3))
        path.lineTo(0, 0.9)
        path.lineTo(1, 0.3)
        path.lineTo(1, 0.9)
        path.closeSubpath()
        painter.drawPath(path)

        prev_brush = painter.brush()
        prev_pen = painter.pen()

        painter.setPen(Qt.NoPen)
        painter.setBrush(self._arrow_brush)
        arrow = QPolygonF(
            [QPointF(0.2, 0),
             QPointF(0.2, 0.20),
             QPointF(0.5, 0.40),
             QPointF(0.8, 0.20),
             QPointF(0.8, 0)
             ]
        )
        painter.drawPolygon(arrow)

        painter.setPen(prev_pen)
        painter.setBrush(prev_brush)
        painter.drawLine(QPointF(0.2, 0), QPointF(0.5, 0.20))
        painter.drawLine(QPointF(0.2, 0.20), QPointF(0.5, 0.40))
        painter.drawLine(QPointF(0.5, 0.20), QPointF(0.8, 0))
        painter.drawLine(QPointF(0.5, 0.40), QPointF(0.8, 0.20))

        painter.drawLine(QPointF(0.5, 0.6), QPointF(0.5, 0.0))


class RightAngleManualValveSymbolIcon(BaseSymbolIcon):
    """
    A widget with a right angle manual valve symbol drawn in it.

    Parameters
    ----------
    parent : QWidget
        The parent widget for the icon
    """
    def draw_icon(self, painter):
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


class NeedleValveSymbolIcon(BaseSymbolIcon):
    """
    A widget with a needle valve symbol drawn in it.

    Parameters
    ----------
    parent : QWidget
        The parent widget for the icon
    """
    def __init__(self, parent=None, **kwargs):
        super(NeedleValveSymbolIcon, self).__init__(parent, **kwargs)
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
        path = QPainterPath(QPointF(0, 0.3))
        path.lineTo(0, 0.9)
        path.lineTo(1, 0.3)
        path.lineTo(1, 0.9)
        path.closeSubpath()
        painter.drawPath(path)
        painter.drawLine(QPointF(0.5, 0.6), QPointF(0.5, 0.15))

        # Draw the arrow end-caps
        painter.setBrush(QBrush(QColor(0, 0, 0)))

        top_arrow_point = QPointF(0.65, 0.36)
        arrow = QPolygonF(
            [QPointF(-0.09, 0.0),
             QPointF(-0.005, 0.0),
             QPointF(-0.005, 0.8),
             QPointF(0.005, 0.8),
             QPointF(0.005, 0.0),
             QPointF(0.09, 0.0),
             QPointF(0.00, -0.25)]
        )

        t = QTransform()
        t.rotate(35)
        top_arrow_r = t.map(arrow)
        arrow_l = top_arrow_r.translated(top_arrow_point)
        painter.drawPolygon(arrow_l)

        painter.setBrush(self._interlock_brush)
        painter.drawRect(QRectF(0.3, 0, 0.4, 0.15))


class ProportionalValveSymbolIcon(BaseSymbolIcon):
    """
    A widget with a proportional valve symbol drawn in it.

    Parameters
    ----------
    parent : QWidget
        The parent widget for the icon
    """
    def __init__(self, parent=None, **kwargs):
        super(ProportionalValveSymbolIcon, self).__init__(parent, **kwargs)
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
        path = QPainterPath(QPointF(0, 0.3))
        path.lineTo(0, 0.9)
        path.lineTo(1, 0.3)
        path.lineTo(1, 0.9)
        path.closeSubpath()
        painter.drawPath(path)
        painter.drawLine(QPointF(0.5, 0.6), QPointF(0.5, 0.15))

        painter.setBrush(self._interlock_brush)
        painter.drawRect(QRectF(0.35, 0, 0.3, 0.3))

        # Draw the arrow end-caps
        painter.setBrush(QBrush(QColor(0, 0, 0)))

        top_arrow_point = QPointF(0.65, 0.42)
        arrow = QPolygonF(
            [QPointF(-0.07, 0.0),
             QPointF(-0.005, 0.0),
             QPointF(-0.005, 0.8),
             QPointF(0.005, 0.8),
             QPointF(0.005, 0.0),
             QPointF(0.07, 0.0),
             QPointF(0.00, -0.25)]
        )

        t = QTransform()
        t.rotate(40)
        top_arrow_r = t.map(arrow)
        arrow_l = top_arrow_r.translated(top_arrow_point)
        painter.drawPolygon(arrow_l)

        t_x = 0.4
        t_y = 0.05
        painter.drawLines([QLineF(0.0+t_x, 0.0+t_y, 0.0+t_x, 0.2+t_y),
                           QLineF(0.0+t_x, 0.0+t_y, 0.1+t_x, 0.2+t_y),
                           QLineF(0.1+t_x, 0.2+t_y, 0.2+t_x, 0.0+t_y),
                           QLineF(0.2+t_x, 0.0+t_y, 0.2+t_x, 0.2+t_y)])


class ControlValveSymbolIcon(PneumaticValveSymbolIcon):
    """Icon for a Control Valve with readback"""
    def draw_icon(self, painter):
        pen = painter.pen()
        pen.setWidthF(pen.width()*2)
        pen.setCapStyle(Qt.FlatCap)
        painter.setPen(pen)
        # Circle parameters
        radius = 0.3
        center = (0.5, 1 - radius)
        # Draw circle
        painter.drawEllipse(QPointF(*center),
                            radius, radius)
        # X pattern
        quad = math.cos(math.radians(45)) * radius
        painter.drawLine(QLineF(center[0] + quad,
                                center[1] + quad,
                                center[0] - quad,
                                center[1] - quad))
        painter.drawLine(QLineF(center[0] + quad,
                                center[1] - quad,
                                center[0] - quad,
                                center[1] + quad))
        # Interlock Icon
        square_dims = (0.4, 0.2)
        painter.drawLine(QPointF(center[0], center[1] - radius),
                         QPointF(center[0], square_dims[1]))
        painter.setBrush(self._interlock_brush)
        painter.drawRect(QRectF((1 - square_dims[0])/2., 0, *square_dims))


class ControlOnlyValveSymbolIcon(BaseSymbolIcon):
    """Icon for a Control Valve with no readback"""
    def draw_icon(self, painter):
        path = QPainterPath(QPointF(0, 0.3))
        path.lineTo(0, 0.9)
        path.lineTo(1, 0.3)
        path.lineTo(1, 0.9)
        path.closeSubpath()
        painter.drawPath(path)


class PneumaticValveNOSymbolIcon(BaseSymbolIcon):
    """
    A widget with a normally open pneumatic valve symbol drawn in it.

    Parameters
    ----------
    parent : QWidget
        The parent widget for the icon
    """
    def __init__(self, parent=None, **kwargs):
        super(PneumaticValveNOSymbolIcon, self).__init__(parent, **kwargs)
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
        path = QPainterPath(QPointF(0, 0.3))
        path.lineTo(0, 0.9)
        path.lineTo(1, 0.3)
        path.lineTo(1, 0.9)
        path.closeSubpath()
        painter.drawPath(path)
        painter.drawLine(QPointF(0.5, 0.6), QPointF(0.5, 0.3))
        painter.setBrush(self._interlock_brush)
        painter.drawRect(QRectF(0.2, 0, 0.6, 0.3))
        # Draw the N
        n_path = QPainterPath(QPointF(0.25, 0.25))
        n_path.lineTo(0.25, 0.05)
        n_path.lineTo(0.45, 0.25)
        n_path.lineTo(0.45, 0.05)
        painter.drawPath(n_path)

        # Draw the O
        painter.drawEllipse(QPointF(0.65, 0.15), 0.1, 0.1)
