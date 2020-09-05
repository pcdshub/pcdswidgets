import os
import logging
from pydm.widgets.base import PyDMPrimitiveWidget
from pydm.widgets.channel import PyDMChannel
from pydm.utilities import remove_protocol, IconFont
from qtpy.QtCore import Property, Q_ENUMS, QSize
from qtpy.QtGui import QPainter, QCursor
from qtpy.QtWidgets import (QWidget, QFrame, QVBoxLayout, QHBoxLayout,
                            QSizePolicy, QStyle, QStyleOption)

from ..utils import refresh_style

logger = logging.getLogger(__name__)


class ContentLocation:
    """
    Enum Class to be used by the widgets to configure the Controls Content
    Location.
    """
    Hidden = 0
    Top = 1
    Bottom = 2
    Left = 3
    Right = 4


class PCDSSymbolBase(QWidget, PyDMPrimitiveWidget, ContentLocation):
    """
    Base class to be used for all PCDS Symbols.

    Parameters
    ----------
    parent : QWidget
        The parent widget for this symbol.
    """
    EXPERT_OPHYD_CLASS = ""

    Q_ENUMS(ContentLocation)
    ContentLocation = ContentLocation

    def __init__(self, parent=None, **kwargs):
        super(PCDSSymbolBase, self).__init__(parent=parent, **kwargs)
        self._expert_display = None
        self.interlock = None
        self._channels_prefix = None
        self._rotate_icon = False

        self._show_icon = True
        self._show_status_tooltip = True
        self._icon_size = -1
        self._icon = None

        self._icon_cursor = self.setCursor(
            QCursor(IconFont().icon("file").pixmap(16, 16))
        )

        self._expert_ophyd_class = self.EXPERT_OPHYD_CLASS or ""

        self.interlock = QFrame(self)
        self.interlock.setObjectName("interlock")
        self.interlock.setSizePolicy(QSizePolicy.Expanding,
                                     QSizePolicy.Expanding)

        self.controls_frame = QFrame(self)
        self.controls_frame.setObjectName("controls")
        self.controls_frame.setSizePolicy(QSizePolicy.Maximum,
                                          QSizePolicy.Maximum)
        self.setLayout(QVBoxLayout())
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().addWidget(self.interlock)
        if not hasattr(self, '_controls_location'):
            self._controls_location = ContentLocation.Bottom
        self.setup_icon()
        self.assemble_layout()
        self.update_status_tooltip()

    def sizeHint(self):
        """
        Suggested initial size for the widget.

        Returns
        -------
        size : QSize
        """
        return QSize(200, 200)

    @Property(ContentLocation)
    def controlsLocation(self):
        """
        Property controlling where the controls frame will be displayed.

        Returns
        -------
        location : ContentLocation
        """
        return self._controls_location

    @controlsLocation.setter
    def controlsLocation(self, location):
        """
        Property controlling where the controls frame will be displayed.

        Parameters
        ----------
        location : ContentLocation
        """
        if location != self._controls_location:
            self._controls_location = location
            self.assemble_layout()

    @Property(str)
    def channelsPrefix(self):
        """
        The prefix to be used when composing the channels for each of the
        elements of the symbol widget.

        The prefix must include the protocol as well. E.g.: ca://VALVE

        Returns
        -------
        str
        """
        return self._channels_prefix

    @channelsPrefix.setter
    def channelsPrefix(self, prefix):
        """
        The prefix to be used when composing the channels for each of the
        elements of the symbol widget.

        The prefix must include the protocol as well. E.g.: ca://VALVE

        Parameters
        ----------
        prefix : str
            The prefix to be used for the channels.
        """
        if prefix != self._channels_prefix:
            self._channels_prefix = prefix
            self.destroy_channels()
            self.create_channels()

    @property
    def icon(self):
        return self._icon

    @icon.setter
    def icon(self, icon):
        if self._icon != icon:
            self._icon = icon
            self.setup_icon()
            self.iconSize = self.iconSize
            self.assemble_layout()

    @Property(bool)
    def showIcon(self):
        """
        Whether or not to show the symbol icon when rendering the widget.

        Returns
        -------
        bool
        """
        return self._show_icon

    @showIcon.setter
    def showIcon(self, value):
        """
        Whether or not to show the symbol icon when rendering the widget.

        Parameters
        ----------
        value : bool
            Shows the Icon if True, hides it otherwise.
        """
        if value != self._show_icon:
            self._show_icon = value
            if self.icon:
                self.icon.setVisible(self._show_icon)
            self.assemble_layout()

    @Property(bool)
    def showStatusTooltip(self):
        """
        Whether or not to show a detailed status tooltip including the state
        of the widget components such as Interlock, Error, State and more.

        Returns
        -------
        bool
        """
        return self._show_status_tooltip

    @showStatusTooltip.setter
    def showStatusTooltip(self, value):
        """
        Whether or not to show a detailed status tooltip including the state
        of the widget components such as Interlock, Error, State and more.

        Parameters
        ----------
        value : bool
            Displays the tooltip if True.

        """
        if value != self._show_status_tooltip:
            self._show_status_tooltip = value

    @Property(int)
    def iconSize(self):
        """
        The size of the icon in pixels.

        Returns
        -------
        int
        """
        return self._icon_size

    @iconSize.setter
    def iconSize(self, size):
        """
        The size of the icon in pixels.

        Parameters
        ----------
        size : int
            A value > 0 will constrain the size of the icon to the defined
            value.
            If the value is <= 0 it will expand to fill the space available.

        """
        if not self.icon:
            return

        if size <= 0:
            size = - 1
            min_size = 1
            max_size = 999999
            self.icon.setSizePolicy(QSizePolicy.Expanding,
                                    QSizePolicy.Expanding)
            self.icon.setMinimumSize(min_size, min_size)
            self.icon.setMaximumSize(max_size, max_size)

        else:
            self.icon.setFixedSize(size, size)
            self.icon.setSizePolicy(QSizePolicy.Fixed,
                                    QSizePolicy.Fixed)

        self._icon_size = size
        self.icon.update()

    @Property(bool)
    def rotateIcon(self):
        """
        Rotate the icon 90 degrees clockwise

        Returns
        -------
        rotate : bool
        """
        return self._rotate_icon

    @rotateIcon.setter
    def rotateIcon(self, rotate):
        """
        Rotate the icon 90 degrees clockwise

        Parameters
        ----------
        rotate : bool
        """
        self._rotate_icon = rotate
        angle = 90 if self._rotate_icon else 0
        if self.icon:
            self.icon.rotation = angle

    @Property(str)
    def expertOphydClass(self):
        """
        The full qualified name of the Ophyd class to be used for the Expert
        screen to be generated using Typhos.

        Returns
        -------
        str
        """
        klass = self._expert_ophyd_class
        if isinstance(klass, type):
            return f"{klass.__module__}.{klass.__name__}"
        return klass

    @expertOphydClass.setter
    def expertOphydClass(self, klass):
        """
        The full qualified name of the Ophyd class to be used for the Expert
        screen to be generated using Typhos.

        Parameters
        ----------
        klass : bool
        """
        if self.expertOphydClass != klass:
            self._expert_ophyd_class = klass

    def paintEvent(self, evt):
        """
        Paint events are sent to widgets that need to update themselves,
        for instance when part of a widget is exposed because a covering
        widget was moved.

        This method handles the painting with parameters from the stylesheet.

        Parameters
        ----------
        evt : QPaintEvent
        """
        painter = QPainter(self)
        opt = QStyleOption()
        opt.initFrom(self)
        self.style().drawPrimitive(QStyle.PE_Widget, opt, painter, self)
        painter.setRenderHint(QPainter.Antialiasing)
        super(PCDSSymbolBase, self).paintEvent(evt)

    def clear(self):
        """
        Remove all inner widgets from the interlock frame layout.
        """
        if not self.interlock:
            return
        layout = self.interlock.layout()
        if layout is None:
            return
        while layout.count() != 0:
            item = layout.itemAt(0)
            if item is not None:
                layout.removeItem(item)

        # Trick to remove the existing layout by re-parenting it in an
        # empty widget.
        QWidget().setLayout(self.interlock.layout())

    def assemble_layout(self):
        """
        Assembles the widget's inner layout depending on the ContentLocation
        and other configurations set.

        """
        if not self.interlock:
            return
        self.clear()

        # (Layout, items)
        widget_map = {
            ContentLocation.Hidden: (QVBoxLayout,
                                     [self.icon]),
            ContentLocation.Top: (QVBoxLayout,
                                  [self.controls_frame,
                                   self.icon]),
            ContentLocation.Bottom: (QVBoxLayout,
                                     [self.icon,
                                      self.controls_frame]),
            ContentLocation.Left: (QHBoxLayout,
                                   [self.controls_frame,
                                    self.icon]),
            ContentLocation.Right: (QHBoxLayout,
                                    [self.icon,
                                     self.controls_frame]),
        }

        layout = widget_map[self._controls_location][0]()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.interlock.setLayout(layout)

        widgets = widget_map[self._controls_location][1]

        # Hide the controls box if they are not going to be included in layout
        controls_visible = self._controls_location != ContentLocation.Hidden
        self.controls_frame.setVisible(controls_visible)

        for widget in widgets:
            if widget is None:
                continue
            # Each widget is in a separate layout to help with expansion rules
            box_layout = QHBoxLayout()
            box_layout.addWidget(widget)
            layout.addLayout(box_layout)

    def setup_icon(self):
        if not self.icon:
            return
        self.icon.setMinimumSize(16, 16)
        self.icon.setSizePolicy(QSizePolicy.Expanding,
                                QSizePolicy.Expanding)
        self.icon.setVisible(self._show_icon)
        self.iconSize = 32
        if hasattr(self.icon, 'clicked'):
            self.icon.clicked.connect(self._handle_icon_click)
            if self._expert_display is not None:
                self.icon.setCursor(self._icon_cursor)

    def _handle_icon_click(self):
        if not self.channelsPrefix:
            logger.error('No channel prefix specified.'
                         'Cannot proceed with opening expert screen for %s.',
                         self.__class__.__name__)
            return

        if self._expert_display is not None:
            logger.debug('Bringing existing display to front.')
            self._expert_display.show()
            self._expert_display.raise_()
            return

        prefix = remove_protocol(self.channelsPrefix)
        klass = self.expertOphydClass
        if not klass:
            logger.error('No expertOphydClass specified for pcdswidgets %s',
                         self.__class__.__name__)
            return
        name = prefix.replace(':', '_')

        try:
            import typhos
        except ImportError:
            logger.error('Typhos not installed. Cannot create display.')
            return

        kwargs = {"name": name, "prefix": prefix}
        display = typhos.TyphosDeviceDisplay.from_class(klass, **kwargs)
        self._expert_display = display
        display.destroyed.connect(self._cleanup_expert_display)

        if display:
            display.show()

    def _cleanup_expert_display(self, *args, **kwargs):
        self._expert_display = None

    def status_tooltip(self):
        """
        Assemble and returns the status tooltip for the symbol.

        Returns
        -------
        str
        """
        status = ""
        if hasattr(self, 'NAME'):
            status = self.NAME
        if status:
            status += os.linesep
        status += "PV Prefix: {}".format(self.channelsPrefix)
        return status

    def destroy_channels(self):
        """
        Method invoked when the channels associated with the widget must be
        destroyed.
        """
        for v in self.__dict__.values():
            if isinstance(v, PyDMChannel):
                v.disconnect()

    def create_channels(self):
        """
        Method invoked when the channels associated with the widget must be
        created.
        This method must be implemented on the subclasses and mixins as needed.
        By default this method does nothing.
        """
        pass

    def update_stylesheet(self):
        """
        Invoke the stylesheet update process on the widget and child widgets to
        reflect changes on the properties.
        """
        refresh_style(self)

    def update_status_tooltip(self):
        """
        Set the tooltip on the symbol to the content of status_tooltip.
        """
        self.setToolTip(self.status_tooltip())
