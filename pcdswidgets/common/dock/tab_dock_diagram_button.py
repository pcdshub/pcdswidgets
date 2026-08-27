"""A dock button with a standard beamline device symbol rendered"""

from enum import IntEnum, auto

from pydm.widgets.channel import PyDMChannel
from qtpy.QtCore import Q_ENUMS, QRect, Qt
from qtpy.QtGui import QCloseEvent, QPainter, QPaintEvent, QPalette, QPen, QPixmap
from qtpy.QtWidgets import QSizePolicy, QWidget

from pcdswidgets.icons.beamline import ATTENUATOR_PATH, IMAGER_PATH, REFLASER_PATH, SLITS_PATH

from .tab_dock_button import TabDockButton

try:
    from qtpy.QtCore import Property  # type: ignore
except ImportError:
    from qtpy.QtCore import pyqtProperty as Property  # type: ignore


class DiagramOption(IntEnum):
    """
    Options for which diagram to show on the widget.

    If you want to add a new option:
    - Add an entry here, note that order/count don't affect anything and won't break old screens.
      (Old screens need the old enum name to exist and nothing more)
    - Copy the new entry into the enums specified at the top of the class body below
    - Add a new png to pcdswidgets/icons/beamline
    - Add corresponding entry to pcdswidgets/icons/beamline/__init__.py
    - Update setDiagram appropriately
    - Update the test suite appropriately
    """

    BLANK = auto()
    ATTENUATOR = auto()
    IMAGER = auto()
    REFLASER = auto()
    SLITS = auto()


class TabDockDiagramButton(TabDockButton):
    """
    Behaves identically to TabDockButton, but renders a standard symbol and lightpath info.
    """

    Q_ENUMS(DiagramOption)
    DiagramOption = DiagramOption
    BLANK = DiagramOption.BLANK
    ATTENUATOR = DiagramOption.ATTENUATOR
    IMAGER = DiagramOption.IMAGER
    REFLASER = DiagramOption.REFLASER
    SLITS = DiagramOption.SLITS

    _qt_designer = {
        "group": "ECS Common Dock",
        "is_container": False,
    }

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._image_pixmap: QPixmap | None = None
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.setFlat(True)
        self.setDiagram(DiagramOption.BLANK)
        self._lightpath_channel_obj = None
        self.setLightpathChannel("")

    def readDiagram(self) -> DiagramOption:
        """Returns the enum of the diagram that is currently in-use."""
        return self._diagram

    def setDiagram(self, diagram: DiagramOption) -> None:
        """Sets the enum of the diagram to use."""
        match diagram:
            case DiagramOption.BLANK:
                self._image_pixmap = None
            case DiagramOption.ATTENUATOR:
                self._image_pixmap = QPixmap(ATTENUATOR_PATH)
            case DiagramOption.IMAGER:
                self._image_pixmap = QPixmap(IMAGER_PATH)
            case DiagramOption.REFLASER:
                self._image_pixmap = QPixmap(REFLASER_PATH)
            case DiagramOption.SLITS:
                self._image_pixmap = QPixmap(SLITS_PATH)
            case _:
                raise ValueError(
                    f"Invalid diagram option {diagram}, options are: {','.join(item for item in DiagramOption)}"
                )
        self._diagram = diagram
        self.repaint()

    diagram = Property(DiagramOption, readDiagram, setDiagram)

    def readLightpathChannel(self) -> str:
        """Returns the channel used to determine if beam is reaching this widget."""
        return self._lightpath_channel_text

    def setLightpathChannel(self, ch: str) -> None:
        """Selects the channel used to determine if beam is reaching this widget."""
        if not ch:
            self._lightpath_channel_text = ch
            if self._lightpath_channel_obj is not None:
                self._lightpath_channel_obj.disconnect()
            self._lightpath_channel_obj = None
            self._lightpath_status = None
            return
        if ch == self._lightpath_channel_text:
            return
        self._lightpath_channel_text = ch
        self._lightpath_status = False
        if self._lightpath_channel_obj is not None:
            self._lightpath_channel_obj.disconnect()
        self._lightpath_channel_obj = PyDMChannel(
            address=self._lightpath_channel_text, value_slot=self.new_lightpath_state
        )
        self._lightpath_channel_obj.connect()
        self.repaint()

    lightpath_channel = Property(str, readLightpathChannel, setLightpathChannel)

    def new_lightpath_state(self, value: bool):
        """Callback to update the visuals of the lightpath indicator when the channel value changes."""
        self._lightpath_status = value
        self.repaint()

    def paintEvent(self, a0: QPaintEvent) -> None:
        """Render the image and the lightpath indicator when it's time to paint this widget."""
        self.setFlat(True)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        # Draw the image first
        self.draw_image(painter=painter)
        # Draw the lightpath indicator on top of the image
        self.draw_lightpath_indicator(painter=painter)
        # Draw the text on top of the image too
        return super().paintEvent(a0)

    def draw_image(self, painter: QPainter):
        """
        Render the selected diagram widget.

        This will be a QPixmap at the bottom-center of the widget bounds,
        and it will also include the widget background-color rendered
        behind the "square" portion of the diagram.
        """
        if self._image_pixmap is None:
            return
        # Align image with bottom horizontal center and scale as big as will fit
        try:
            image_ratio = self._image_pixmap.height() / self._image_pixmap.width()
        except ZeroDivisionError:
            return
        if image_ratio == 0:
            return
        height_if_full_width = self.width() * image_ratio
        if height_if_full_width <= self.height():
            draw_width = self.width()
            draw_height = int(height_if_full_width)
        else:
            draw_width = int(self.height() / image_ratio)
            draw_height = self.height()
        # Draw the background color in the lower square
        # This usually is unset and ends up being grey
        painter.save()
        bg_color = self.palette().color(QPalette.Background)
        painter.setBrush(bg_color)
        sq_side = min(draw_height, draw_width)
        painter.drawRect(QRect((self.width() - sq_side) // 2, self.height() - sq_side, sq_side, sq_side))
        painter.restore()
        painter.drawPixmap(
            QRect((self.width() - draw_width) // 2, self.height() - draw_height, draw_width, draw_height),
            self._image_pixmap,
        )

    def draw_lightpath_indicator(self, painter: QPainter):
        """
        Render the lightpath state.

        This will be an ellipse at the top-left of the widget bounds,
        filled with cyan if the lightpath channel is "true".
        """
        painter.save()
        if self._lightpath_status is None:
            return
        indicator_size = int(min(self.width(), self.height()) / 5)
        if not indicator_size:
            return
        pen = QPen()
        pen_width = max(1, int(indicator_size * 0.10))
        pen.setWidth(pen_width)
        painter.setPen(pen)
        if self._lightpath_status:
            painter.setBrush(Qt.cyan)
        painter.drawEllipse(pen_width, pen_width, indicator_size, indicator_size)
        painter.restore()

    def closeEvent(self, a0: QCloseEvent) -> None:
        """On close, clean up the pydm channel."""
        if self._lightpath_channel_obj is not None:
            self._lightpath_channel_obj.disconnect()
        return super().closeEvent(a0)

    def setFlat(self, a0: bool) -> None:
        """Prevent flat = False which interferes with our rendering."""
        super().setFlat(True)
