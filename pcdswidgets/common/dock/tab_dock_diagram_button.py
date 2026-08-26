"""A dock button with a standard beamline device symbol rendered"""

from enum import IntEnum

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
    BLANK = 0
    ATTENUATOR = 1
    IMAGER = 2
    REFLASER = 3
    SLITS = 4


class TabDockDiagramButton(TabDockButton):
    """
    Behaves identically to TabDockButton, but renders a standard symbol.
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
        self.setLightpathChannel("")

    def readDiagram(self) -> DiagramOption:
        return self._diagram

    def setDiagram(self, diagram: DiagramOption) -> None:
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

    diagram = Property(DiagramOption, readDiagram, setDiagram)

    def readLightpathChannel(self) -> str:
        return self._lightpath_channel_text

    def setLightpathChannel(self, ch: str) -> None:
        if not ch:
            self._lightpath_channel_text = ch
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
        self._lightpath_status = value
        self.repaint()

    def paintEvent(self, a0: QPaintEvent) -> None:
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
        if self._lightpath_channel_obj is not None:
            self._lightpath_channel_obj.disconnect()
        return super().closeEvent(a0)

    def setFlat(self, a0: bool) -> None:
        """Prevent flat = False which interferes with our rendering."""
        super().setFlat(True)
