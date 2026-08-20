"""A dock button with a standard beamline device symbol rendered"""

from enum import IntEnum

from pydm.widgets.drawing import PyDMDrawingImage
from qtpy.QtCore import Q_ENUMS, Qt
from qtpy.QtWidgets import QSizePolicy, QVBoxLayout, QWidget

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
        layout = QVBoxLayout()
        self._image = PyDMDrawingImage(parent=self)
        self._image.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        layout.addWidget(self._image)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.setDiagram(DiagramOption.BLANK)

    def readDiagram(self) -> DiagramOption:
        return self._diagram

    def setDiagram(self, diagram: DiagramOption) -> None:
        self._image.show()
        match diagram:
            case DiagramOption.BLANK:
                self._image.hide()
            case DiagramOption.ATTENUATOR:
                self._image.setFilename(ATTENUATOR_PATH)
            case DiagramOption.IMAGER:
                self._image.setFilename(IMAGER_PATH)
            case DiagramOption.REFLASER:
                self._image.setFilename(REFLASER_PATH)
            case DiagramOption.SLITS:
                self._image.setFilename(SLITS_PATH)
            case _:
                raise ValueError(
                    f"Invalid diagram option {diagram}, options are: {','.join(item for item in DiagramOption)}"
                )
        self._diagram = diagram

    diagram = Property(DiagramOption, readDiagram, setDiagram)
