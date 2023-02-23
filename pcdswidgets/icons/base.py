from pydm.utilities import is_qt_designer, remove_protocol
from qtpy.QtCore import Property, QEvent, QSize, Qt, Signal
from qtpy.QtGui import QBrush, QColor, QPainter, QPen
from qtpy.QtWidgets import (QApplication, QStyle, QStyleOption, QToolTip,
                            QWidget)

from ..utils import find_ancestor_for_widget


class BaseSymbolIcon(QWidget):
    """
    Base class to be used for all the Symbol Icon widgets.
    This class holds most of the properties to be exposed and takes care of 90%
    of the drawing code needed.

    Parameters
    ----------
    parent : QWidget
        The parent widget for this widget.
    """
    clicked = Signal()

    def __init__(self, parent=None):
        self._brush = QBrush(QColor(0, 255, 0), Qt.SolidPattern)
        self._original_brush = None
        self._rotation = 0
        self._pen_style = Qt.SolidLine
        self._pen = QPen(self._pen_style)
        self._pen.setCosmetic(True)
        self._pen_width = 1.0
        self._pen_color = QColor(0, 0, 0)
        self._pen.setWidthF(self._pen_width)
        self._pen.setColor(self._pen_color)
        self._original_pen_style = self._pen_style
        self._original_pen_color = self._pen_color
        super().__init__(parent=parent)
        self.setObjectName("icon")
        if not is_qt_designer():
            # We should  install the Event Filter only if we are running
            # and not at the Designer
            self.installEventFilter(self)

    def eventFilter(self, obj, event):
        """
        EventFilter to redirect "middle click" to :meth:`.show_address_tooltip`
        """
        # Override the eventFilter to capture all middle mouse button events,
        # and show a tooltip if needed.
        if event.type() == QEvent.MouseButtonPress:
            if event.button() == Qt.MiddleButton:
                self.show_state_channel(event)
                return True
        return False

    def show_state_channel(self, event):
        """
        Show the State Channel Tooltip and copy address to clipboard

        This is intended to replicate the behavior of the "middle click" from
        EDM. If the parent is not PCDSSymbolBase and does not have a valid
        State Channel nothing will be displayed.
        """
        from ..vacuum.base import PCDSSymbolBase

        p = find_ancestor_for_widget(self, PCDSSymbolBase)
        if not p:
            return

        state_suffix = getattr(p, '_state_suffix', None)
        if not state_suffix:
            return

        addr = f"{p.channelsPrefix}{state_suffix}"
        QToolTip.showText(event.globalPos(), addr)
        # If the address has a protocol, strip it out before putting it on the
        # clipboard.
        copy_text = remove_protocol(addr)

        clipboard = QApplication.clipboard()
        clipboard.setText(copy_text)
        event = QEvent(QEvent.Clipboard)
        QApplication.instance().sendEvent(clipboard, event)

    def minimumSizeHint(self):
        return QSize(32, 32)

    def paintEvent(self, event):
        """
        Paint events are sent to widgets that need to update themselves,
        for instance when part of a widget is exposed because a covering
        widget was moved.

        This method handles the painting with parameters from the stylesheet,
        configures the brush, pen and calls ```draw_icon``` so the specifics
        can be performed for each of the drawing classes.

        Parameters
        ----------
        event : QPaintEvent
        """
        opt = QStyleOption()
        opt.initFrom(self)
        painter = QPainter(self)
        painter.setClipping(True)
        self.style().drawPrimitive(QStyle.PE_Widget, opt, painter, self)
        painter.setRenderHint(QPainter.Antialiasing)
        w = self.width()
        h = self.height()
        painter.translate(w / 2.0, h / 2.0)
        painter.rotate(self._rotation)
        painter.translate(-w / 2.0, -h / 2.0)
        painter.translate(self._pen_width / 2.0, self._pen_width / 2.0)
        painter.scale(w - self._pen_width, h - self._pen_width)
        painter.translate(0, 0)
        painter.setBrush(self._brush)
        painter.setPen(self._pen)
        self.draw_icon(painter)

        QWidget.paintEvent(self, event)

    def draw_icon(self, painter):
        """
        Method responsible for the drawing of the icon part of the paintEvent.
        This method must be implemented by the symbol icon widgets to include
        their specific drawings.

        Parameters
        ----------
        painter : QPainter
        """
        raise NotImplementedError("draw_icon must be implemented by subclass")

    @Property(QBrush)
    def brush(self):
        """
        PyQT Property for the brush object to be used when coloring the
        drawing

        Returns
        -------
        QBrush
        """
        return self._brush

    @brush.setter
    def brush(self, new_brush):
        """
        PyQT Property for the brush object to be used when coloring the
        drawing

        Parameters
        ----------
        new_brush : QBrush
        """
        if new_brush != self._brush:
            self._brush = new_brush
            self.update()

    @Property(Qt.PenStyle)
    def penStyle(self):
        """
        PyQT Property for the pen style to be used when drawing the border

        Returns
        -------
        int
            Index at Qt.PenStyle enum
        """
        return self._pen_style

    @penStyle.setter
    def penStyle(self, new_style):
        """
        PyQT Property for the pen style to be used when drawing the border

        Parameters
        ----------
        new_style : int
            Index at Qt.PenStyle enum
        """
        if new_style != self._pen_style:
            self._pen_style = new_style
            self._pen.setStyle(new_style)
            self.update()

    @Property(QColor)
    def penColor(self):
        """
        PyQT Property for the pen color to be used when drawing the border

        Returns
        -------
        QColor
        """
        return self._pen_color

    @penColor.setter
    def penColor(self, new_color):
        """
        PyQT Property for the pen color to be used when drawing the border

        Parameters
        ----------
        new_color : QColor
        """
        if new_color != self._pen_color:
            self._pen_color = new_color
            self._pen.setColor(new_color)
            self.update()

    @Property(float)
    def penWidth(self):
        """
        PyQT Property for the pen width to be used when drawing the border

        Returns
        -------
        float
        """
        return self._pen_width

    @penWidth.setter
    def penWidth(self, new_width):
        """
        PyQT Property for the pen width to be used when drawing the border

        Parameters
        ----------
        new_width : float
        """
        if new_width < 0:
            return
        if new_width != self._pen_width:
            self._pen_width = int(new_width)
            self._pen.setWidth(self._pen_width)
            self.update()

    @Property(float)
    def rotation(self):
        """
        PyQt Property for the rotation.
        This rotates the icon coordinate system clockwise.

        Returns
        -------
        angle : float
            The angle in degrees
        """
        return self._rotation

    @rotation.setter
    def rotation(self, angle):
        """
        PyQt Property for the rotation.
        This rotates the icon coordinate system clockwise.

        Parameters
        ----------
        angle : float
            The angle in degrees
        """
        self._rotation = angle
        self.update()

    def mousePressEvent(self, evt):
        """Clicking the icon fires the ``clicked`` signal"""
        # Default Qt reaction to the icon press
        super().mousePressEvent(evt)
        if evt.button() == Qt.LeftButton:
            self.clicked.emit()
