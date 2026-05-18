"""
Originally generated from jinja template ui_main_widget.j2

This file can be safely edited to change the runtime behavior of the widget.
"""
import logging

from qtpy import QtWidgets

from pcdswidgets.builder.designer_options import DesignerOptions
from pcdswidgets.builder.icon_options import IconOptions
from pcdswidgets.generated.imaging.common.camera_viewer_stretch_base import (
    CameraViewerStretchBase,
)

logger = logging.getLogger(__name__)

class CameraViewerStretch(CameraViewerStretchBase):

    sidebar_toggle: QtWidgets.QPushButton
    sidebar_scroll: QtWidgets.QScrollArea

    designer_options = DesignerOptions(
        group="ECS Imaging Common",
        is_container=False,
        icon=IconOptions.NONE,
    )

    _qt_designer_ = {
        "group": "ECS Imaging",
        "is_container": True,
    }

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self._current_stream = "IMAGE1:ArrayData"
        self._current_protocol = "ca"
        self._frame_count = 0
        self._signals_connected = False

        self.sidebar_toggle.toggled.connect(self._toggle_sidebar)

    def _toggle_sidebar(self, checked: bool) -> None:
        self.sidebar_scroll.setVisible(checked)
