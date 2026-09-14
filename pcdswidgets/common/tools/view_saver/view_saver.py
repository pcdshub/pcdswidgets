"""ViewSaver widget — persists and restores widget states via QSettings."""

import logging
import os
import random
import string
from pathlib import Path
from typing import Any

from pydm.utilities import is_qt_designer
from pydm.utilities.iconfont import IconFont
from pydm.widgets.base import PyDMPrimitiveWidget
from pydm.widgets.designer_settings import update_property_for_widget
from qtpy.QtCore import Property, QSettings, QSize, Qt, QTimer
from qtpy.QtGui import QColor, QFont, QIcon, QMouseEvent, QPainter, QPen
from qtpy.QtWidgets import QSizePolicy, QWidget

from .edit_bindings_extension import EditWidgetListExtension
from .registry import discover_widgets, resolve_widget
from .view_saver_dialog import ViewSaverDialog

logger = logging.getLogger(__name__)

POLL_INTERVAL_MS = 10_000


class ViewSaver(QWidget, PyDMPrimitiveWidget):
    """
    Adds automated save and restore to sibling widget's
    view-state properties using QSettings.

    In QtDesigner this widget is visible as a small box.

    In designer, double clicking opens a dialog to select widget names
    to be saved. (allows users to select only widgets that need persistance)

    At runtime it hides itself but polls watched widgets, writing
    changed values to disk.

    At the first UI restores previous saved state.

    registry.REGISTRY dict maps properties that
    should be persisted given a widget class.

    Designer properties
    -------------------
    dirName : str
        Directory where the settings .ini file is stored
        (default ``~/.config/pcds_view_saves``).
    fileName : str
        Name of the .ini file (without extension).  Supports PyDM
        ``${MACRO}`` expansion and this is recommended in situations the same UI
        screen is used for different devices
        Auto-generated rand on first load
    _widget_list : list[str]
        List of target sibling widgets to persist
    """

    _qt_designer_ = {
        "group": "ECS Common Tools",
        "is_container": False,
        "extensions": [EditWidgetListExtension],
    }

    _HINT_TEXT = "ViewSaver\nDouble-click to edit\n(hidden at runtime)"

    @classmethod
    def get_designer_icon(cls) -> QIcon:
        return IconFont().icon("save")

    def __init__(self, parent: QWidget | None = None, **kwargs: Any):
        super().__init__(parent=parent, **kwargs)

        self._dir_name: str = os.path.join("~",".config", "pcds_view_saves")
        self._file_name: str = ""
        self._tracked_widgets = {}
        self._loaded: bool = False
        self._last_snapshot: dict[str, Any] = {}

        # Poll timer — started in _initial_load
        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(POLL_INTERVAL_MS)
        self._poll_timer.timeout.connect(self._poll)

        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        # Defer setup to the next event-loop cycle.
        # ensures fileName loaded from .ui file and sibling widgets exist
        QTimer.singleShot(0, self._deferred_init)

    def _deferred_init(self) -> None:
        """Run mode-appropriate setup once the event loop resumes."""
        if is_qt_designer():
            # Stay visible and on top so it's easy to find
            self.raise_()
            self._ensure_default_file_name()
        else:
            self._initial_load()

    def _ensure_default_file_name(self) -> None:
        """Assign a semi-unique default fileName if none was loaded from the .ui
        """
        if self._file_name:
            return

        suffix = "".join(random.choices(string.ascii_letters + "123456789", k=8))
        self._file_name = f"view_saver_{suffix}"
        # informs designer the property has changed so it will be saved.
        update_property_for_widget(self, "fileName", self._file_name)

    def _build_settings(self) -> QSettings | None:
        """Build a QSettings object in IniFormat, or None macros are not expanded."""
        name = self._file_name
        if not name or "${" in name:
            logger.error("View save path not initialized.")
            return None
        dir_path = Path(os.path.expanduser(os.path.expandvars(self._dir_name)))
        ini_path = str(dir_path / f"{name}.ini")
        return QSettings(ini_path, QSettings.IniFormat)

    def _initial_load(self) -> None:
        self.hide()
        settings = self._build_settings()
        if settings is None:
            return
        for widget_name in list(self._tracked_widgets.keys()):
            # resolve widget attributes
            prop_list = resolve_widget(self.window(), widget_name)
            self._tracked_widgets[widget_name] = prop_list
            if prop_list is None:
                continue
            # restore any saved settings
            for prop_name, (_getter, setter) in prop_list.items():
                saved_val = settings.value(f"{widget_name}/{prop_name}")
                try:
                    if saved_val is not None:
                        setter(saved_val)
                except Exception:
                    logger.exception(f"ViewSaver: failed to restore {widget_name}/{prop_name}")
        self._loaded = True
        self._poll_timer.start()

    def _poll(self) -> None:
        settings = self._build_settings()
        if settings is None:
            return
        for widget_name, prop_list in self._tracked_widgets.items():
            if prop_list is None:
                continue
            for prop_name, (getter, _setter) in prop_list.items():
                try:
                    settings.setValue(f"{widget_name}/{prop_name}", getter())
                except Exception:
                    logger.exception(f"ViewSaver: failed to save {widget_name}/{prop_name}")

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        """Open the settings editor on double-click."""
        dialog = ViewSaverDialog(
            available_widgets=discover_widgets(self.window()),
            existing_widgets=list(self._tracked_widgets.keys()),
            dir_name=self._dir_name,
            file_name=self._file_name,
            parent=self,
        )
        if dialog.exec_():
            # set properties based on result
            dir_name, file_name, widget_names = dialog.results()
            self.dirName = dir_name
            self.fileName = file_name
            self.widget_names = widget_names
            # informs designer the properties have changed for saves to ui file.
            update_property_for_widget(self, "dirName", self._dir_name)
            update_property_for_widget(self, "fileName", self._file_name)
            update_property_for_widget(
                self, "widget_names", list(self._tracked_widgets.keys())
            )

    def closeEvent(self, event) -> None:  # noqa: N802
        if not is_qt_designer():
            self._poll()
        super().closeEvent(event)

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def sizeHint(self) -> QSize:  # noqa: N802
        return QSize(120, 48)

    def minimumSizeHint(self) -> QSize:  # noqa: N802
        return QSize(120, 48)

    def paintEvent(self, event) -> None:  # noqa: N802
        """Draw a simple label for interacting with this widget in designer."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Background
        painter.setPen(QPen(QColor(80, 80, 80)))
        painter.setBrush(QColor(230, 240, 255))
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 6, 6)

        # Text
        font = QFont()
        font.setPointSize(8)
        painter.setFont(font)
        painter.setPen(QColor(40, 40, 40))
        painter.drawText(self.rect(), Qt.AlignCenter, self._HINT_TEXT)
        painter.end()

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    def _get_dir_name(self) -> str:
        return self._dir_name

    def _set_dir_name(self, value: str) -> None:
        self._dir_name = value

    dirName = Property("QString", _get_dir_name, _set_dir_name)

    def _get_file_name(self) -> str:
        return self._file_name

    def _set_file_name(self, value: str) -> None:
        self._file_name = value

    fileName = Property("QString", _get_file_name, _set_file_name)

    def _get_widget_names(self) -> list[str]:
        return list(self._tracked_widgets.keys())

    def _set_widget_names(self, value: list[str]) -> None:
        # defer resolving attr names until runtime load
        self._tracked_widgets = dict.fromkeys(value)

    widget_names = Property("QStringList", _get_widget_names, _set_widget_names)
