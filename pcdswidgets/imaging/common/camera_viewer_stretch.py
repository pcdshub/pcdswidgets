"""
Originally generated from jinja template ui_main_widget.j2

This file can be safely edited to change the runtime behavior of the widget.
"""

import logging
from collections import deque

from pydm.utilities import is_qt_designer
from pydm.widgets import PyDMImageView
from qtpy import QtWidgets
from qtpy.QtCore import QChildEvent, QEvent, QTimer

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
    display_fps_label: QtWidgets.QLabel

    designer_options = DesignerOptions(
        group="ECS Imaging Common",
        is_container=True,
        icon=IconOptions.camera,
    )

    # names of base widgets in this class
    _internal_widget_names: set[str] = set()

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        self._initializing = True
        self._adopted_widgets: list[QtWidgets.QWidget] = []
        super().__init__(parent)
        self._frame_count = 0
        self._fps_rolling_buffer = deque(maxlen=5)
        self._first_show = True

        # snapshot internal widgets to distinguish them from added widgets
        if not CameraViewerStretch._internal_widget_names:
            CameraViewerStretch._internal_widget_names = {
                child.objectName() for child in self.findChildren(QtWidgets.QWidget) if child.objectName()
            }

        # Display FPS timer
        self._fps_timer = QTimer(self)
        self._fps_timer.setInterval(1000)
        self._fps_timer.timeout.connect(self._update_display_fps)
        self._fps_timer.start()  # Connect image update signal for FPS counting
        try:
            self.image_view.newImageSignal.connect(self._on_new_image)
        except AttributeError:
            # some pydm versions may not have this signal
            pass

        self.sidebar_toggle.toggled.connect(self._toggle_sidebar)
        self._initializing = False

    def set_cam_prefix(self, value: str) -> None:
        """Override to propagate cam_prefix to adopted sub-widgets."""
        super().set_cam_prefix(value)
        self._propagate_cam_prefix(value)

    def _propagate_cam_prefix(self, value: str) -> None:
        """Push cam_prefix to all adopted sub-widgets that accept it."""
        for widget in self._adopted_widgets:
            if hasattr(widget, "cam_prefix"):
                widget.cam_prefix = value

    def _toggle_sidebar(self, checked: bool) -> None:
        self.sidebar_scroll.setVisible(checked)

    # -- Display FPS -------------------------------------------------------

    def _on_new_image(self) -> None:
        self._frame_count += 1

    def _update_display_fps(self) -> None:
        self._fps_rolling_buffer.append(self._frame_count)
        avg_fps = sum(self._fps_rolling_buffer) / len(self._fps_rolling_buffer)
        self.display_fps_label.setText(f"{avg_fps:.1f}")
        self._frame_count = 0

    # -- Sub-Widget Adoption ----------------------------------

    def childEvent(self, event: QChildEvent) -> None:
        """Mark externally added widgets with '_sidebar_widget' for later adoption."""
        super().childEvent(event)
        if self._initializing:
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
        if self._initializing:
            return
        if self._first_show:
            self._first_show = False
            if not is_qt_designer():
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

        # sort all widgets marked as sidebar_widgets by the current y location
        candidates = sorted(
            (
                child
                for child in self.findChildren(QtWidgets.QWidget)
                if child.parent() is self and child.property("_sidebar_widget")
            ),
            key=lambda w: w.y(),
        )
        # add the children in collapsible sections
        cam_prefix = self._macro_values.get("cam_prefix", "")
        for child in candidates:
            section = CollapsibleSection(
                child,
                parent=self.sidebar_scroll.widget(),
                collapsed=True,
            )
            sidebar_layout.addWidget(section)
            section.show()
            self._adopted_widgets.append(child)
            # Propagate cam_prefix to sub-widget at adoption time
            if cam_prefix and hasattr(child, "cam_prefix"):
                child.cam_prefix = cam_prefix
            # Link sub-widget to our image_view if it supports it
            if hasattr(child, "link_image_view"):
                child.link_image_view(self.image_view)
            logger.debug(
                "Adopted child %s as collapsible '%s'",
                child.objectName() or type(child).__name__,
            )
        # add a vertical spacer to push all widgets to the top
        sidebar_layout.addStretch()
