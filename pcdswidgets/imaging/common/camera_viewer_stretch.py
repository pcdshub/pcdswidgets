"""
Originally generated from jinja template ui_main_widget.j2

This file can be safely edited to change the runtime behavior of the widget.
"""

import logging

from pydm.widgets import PyDMImageView
from qtpy import QtWidgets
from qtpy.QtCore import QChildEvent, QEvent

from pcdswidgets.builder.designer_options import DesignerOptions
from pcdswidgets.builder.icon_options import IconOptions
from pcdswidgets.generated.imaging.common.camera_viewer_stretch_base import (
    CameraViewerStretchBase,
)

from .collapsible_section import CollapsibleSection

logger = logging.getLogger(__name__)

CA_SUFFIX = ":ArrayData"
PVA_SUFFIX = "_PVA:Image1"


class CameraViewerStretch(CameraViewerStretchBase):
    sidebar_toggle: QtWidgets.QPushButton
    sidebar_scroll: QtWidgets.QScrollArea
    image_view: PyDMImageView

    designer_options = DesignerOptions(
        group="ECS Imaging Common",
        is_container=True,
        icon=IconOptions.camera,
    )

    # names of base widgets in this class
    _internal_widget_names: set[str] = set()

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self._frame_count = 0
        self._first_show = True

        # snapshot internal widgets to distinguish them from added widgets
        if not CameraViewerStretch._internal_widget_names:
            CameraViewerStretch._internal_widget_names = {
                child.objectName()
                for child in self.findChildren(QtWidgets.QWidget)
                if child.objectName()
            }

        self.sidebar_toggle.toggled.connect(self._toggle_sidebar)

    def _toggle_sidebar(self, checked: bool) -> None:
        self.sidebar_scroll.setVisible(checked)

    # -- Sub-Widget Adoption ----------------------------------

    def childEvent(self, event: QChildEvent) -> None:
        """Mark externally added widgets with '_sidebar_widget' for later adoption."""
        super().childEvent(event)
        if not self._init_complete:
            return
        if event.type() == QEvent.ChildAdded:
            child = event.child()
            if not isinstance(child, QtWidgets.QWidget):
                return
            if self._is_external(child):
                child.setProperty("_sidebar_widget", True)

    def _is_external(self, widget: QtWidgets.QWidget) -> bool:
        """Return True if widget is NOT one of our known internal children."""
        if widget.parent() is not self:
            return False
        name = widget.objectName()
        if name and name in self._internal_widget_names:
            return False
        # Layouts and spacers get added as children too, these should be ignored
        if isinstance(widget, (QtWidgets.QLayout, QtWidgets.QSpacerItem)):
            return False
        return True

    def showEvent(self, event) -> None:
        """Hooks into the first show event to adopt child widgets added in designer"""
        super().showEvent(event)
        if self._first_show:
            self._first_show = False
            self._adopt_child_widgets()

    def _adopt_child_widgets(self) -> None:
        """
        Move user-dropped widgets from *self* into the sidebar layout.

        Finds all direct children marked with the '_sidebar_widget' dynamic
        property (set by childEvent in Designer or persisted in the .ui file)
        and wraps them in CollapsibleSection widgets inside sidebar_scroll.
        """
        sidebar_layout = self.sidebar_scroll.widget().layout()
        if sidebar_layout is None:
            sidebar_layout = QtWidgets.QVBoxLayout(self.sidebar_scroll.widget())
            sidebar_layout.setContentsMargins(0, 0, 0, 0)
            sidebar_layout.setSpacing(2)

        for child in self.findChildren(QtWidgets.QWidget):
            if child.parent() is not self:
                continue
            if not child.property("_sidebar_widget"):
                continue
            section = CollapsibleSection(
                child,
                parent=self.sidebar_scroll.widget(),
                collapsed=True,
            )
            sidebar_layout.addWidget(section)
            section.show()
            logger.debug(
                "Adopted child %s as collapsible '%s'",
                child.objectName() or type(child).__name__,
            )
        # add a vertical spacer to push all widgets to the top
        sidebar_layout.addStretch()

