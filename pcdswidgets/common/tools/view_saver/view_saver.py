"""ViewSaver widget — persists and restores widget states via QSettings."""

import logging
import os
import random
import string
from pathlib import Path
from typing import Any, Callable

from pydm.utilities import is_qt_designer
from pydm.utilities.iconfont import IconFont
from pydm.widgets.base import PyDMPrimitiveWidget
from pydm.widgets.designer_settings import update_property_for_widget
from qtpy.QtCore import Property, QEvent, QObject, QRect, QSettings, QSize, Qt, QTimer
from qtpy.QtGui import QColor, QFont, QIcon, QPainter, QPaintEvent, QPen
from qtpy.QtWidgets import QAction, QApplication, QFrame, QSizePolicy, QWidget

from .registry import (
    is_registry_container,
    is_registry_savable,
    resolve_registry_props,
)
from .view_saver_dialog import ViewSaverDialog

logger = logging.getLogger(__name__)

POLL_INTERVAL_MS = 60_000


class EditWidgetListExtension:
    """Adds an 'Edit ViewSaver…' action to the Designer right-click menu.

    Follows the same pattern as ``MacroEditExtension`` in
    ``pcdswidgets.builder.designer_widget``.
    """

    def __init__(self, widget: "ViewSaver"):
        self.widget = widget
        self._action = QAction("&Edit ViewSaver\u2026", self.widget)
        self._action.triggered.connect(widget.open_dialog)

    def actions(self) -> list[QAction]:
        return [self._action]


class ViewSaver(QFrame, PyDMPrimitiveWidget):
    """
    An invisible container that auto-saves and restores the view-state of the
    widgets placed inside it, using QSettings.

    Drop this widget onto a screen and place the widgets you want persisted
    inside it.

    Any child that exposes a ``get_view_saver_properties`` or
    is registered in ``registry.WIDGET_REGISTRY`` is tracked.

    Optional ``excludedWidgets`` list can
    opt children out.

    In QtDesigner the container draws a dashed border and a small corner label
    so it can be located and edited (double-click, or the right-click task
    menu, opens the settings dialog).  At runtime it is fully transparent with
    no border or margins, so only its child widgets are visible.


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
    excludedWidgets : list[str]
        objectNames of savable child widgets to skip.
    """

    _qt_designer_ = {
        "group": "ECS Common Tools",
        "is_container": True,
        "extensions": [EditWidgetListExtension],
    }

    _HINT_TEXT = "ViewSaver \u2022 Double-click to edit"

    @classmethod
    def get_designer_icon(cls) -> QIcon:
        return IconFont().icon("save")

    def __init__(self, parent: QWidget | None = None, **kwargs: Any):
        super().__init__(parent=parent, **kwargs)

        self._dir_name: str = os.path.join("~", ".config", "pcds_view_saves")
        self._file_name: str = ""
        self._excluded: list[str] = []
        # objectName -> {propKey: (getter, setter)} resolved at runtime load
        self._tracked_widgets: dict[str, dict[str, tuple[Callable, Callable]]] = {}
        self._loaded: bool = False
        self._last_snapshot: dict[str, Any] = {}

        # Invisible passthrough container: no frame, no margins, transparent.
        self.setFrameShape(QFrame.NoFrame)
        self.setContentsMargins(0, 0, 0, 0)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAutoFillBackground(False)

        # Poll timer — started in _initial_load
        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(POLL_INTERVAL_MS)
        self._poll_timer.timeout.connect(self._save_settings)

        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

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
        """Assign a semi-unique default fileName if none was loaded from the .ui"""
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
            logger.error(f"View save path ''{self._file_name}'' not initialized.")
            return None
        dir_path = Path(os.path.expanduser(os.path.expandvars(self._dir_name)))
        ini_path = str(dir_path / f"{name}.ini")
        return QSettings(ini_path, QSettings.IniFormat)

    def _initial_load(self) -> None:
        """non-designer init that happens after all widgets load"""
        settings = self._build_settings()
        if settings is None:
            return
        self._tracked_widgets = self._resolve_tracked_widgets()
        logger.debug(f"ViewSaver: loading from {settings.fileName()} ({len(self._tracked_widgets)} tracked widgets)")
        restored = 0
        for widget_name, prop_dict in self._tracked_widgets.items():
            # restore any saved settings
            for prop_name, (_getter, setter) in prop_dict.items():
                saved_val = settings.value(f"{widget_name}/{prop_name}")
                if saved_val is None:
                    logger.debug(f"No saved value for {widget_name}/{prop_name}")
                    continue
                try:
                    setter(saved_val)
                    restored += 1
                    logger.debug(f"Restored {widget_name}/{prop_name} = {saved_val!r}")
                except Exception:
                    logger.exception(f"Failed to restore {widget_name}/{prop_name}")
        logger.debug(f"Restored {restored} value(s)")
        self._loaded = True
        self._poll_timer.start()

        app = QApplication.instance()
        if app is not None:
            # Backstop for quit paths that tear the display down without ever
            # firing closeEvent (e.g. PyDMMainWindow's File > Quit calling
            # app.quit() directly), so the last poll interval isn't lost.
            app.aboutToQuit.connect(self._flush_on_quit)

        # closeEvent is only delivered to the top-level window, never to this
        # hidden child widget, so watch the container window instead to catch
        # the user closing just this screen while the app keeps running.
        window = self.window()
        if window is not None:
            window.installEventFilter(self)

    def _flush_on_quit(self) -> None:
        """Write current widget state before the application exits."""
        if not self._loaded:
            return
        logger.debug("aboutToQuit fired, saving view to file.")
        self._save_settings()

    def _save_settings(self) -> None:
        settings = self._build_settings()
        if settings is None:
            return
        saved = 0
        for widget_name, prop_list in self._tracked_widgets.items():
            if prop_list is None:
                continue
            for prop_name, (getter, _setter) in prop_list.items():
                try:
                    val = getter()
                    settings.setValue(f"{widget_name}/{prop_name}", val)
                    saved += 1
                    logger.debug(f"Saved {widget_name}/{prop_name} = {val!r}")
                except Exception:
                    logger.exception(f"Failed to save {widget_name}/{prop_name}")
        logger.debug(f"Wrote {saved} value(s) to {settings.fileName()}")

    # ------------------------------------------------------------------
    # Widget Discovery
    # ------------------------------------------------------------------

    def _walk_widget_tree(self) -> list[QWidget]:
        """Return every savable descendant.

        A widget is savable if it defines ``get_view_saver_properties`` or
        if its class is listed in ``WIDGET_REGISTRY``.

        The child tree is walked manually so it stops as soon as a widget is
        found savable. Non-savable containers and registered/duck-typed
        containers are descended into recursively.
        """
        found: list[QWidget] = []

        def _walk(widget: QWidget) -> None:
            for child in widget.children():
                if not isinstance(child, QWidget):
                    continue
                # check if widget is saveable
                if hasattr(child, "get_view_saver_properties") or is_registry_savable(child):
                    found.append(child)
                    # A savable container still holds nested savables; keep
                    # descending otherwise stop.
                    if getattr(child, "VIEW_SAVER_IS_CONTAINER", False) or is_registry_container(child):
                        _walk(child)
                else:
                    _walk(child)

        _walk(self)
        return found

    def _walk_widget_names(self) -> list[str]:
        """Return the objectName of every savable descendant, skipping unnamed ones."""
        return [name for w in self._walk_widget_tree() if (name := w.objectName())]

    def _resolve_tracked_widgets(self) -> dict[str, dict[str, tuple[Callable, Callable]]]:
        """Resolve savable child widgets into ``{objectName: {prop: (get, set)}}``.

        Walks the child tree and resolve the getter/setter for each saveable widget's
        properties.

        Skips any excluded objectNames, and warns for savable widgets that lack an
        objectName since they cannot be keyed in the settings file.
        """
        resolved: dict[str, dict[str, tuple[Callable, Callable]]] = {}
        for widget in self._walk_widget_tree():
            name = widget.objectName()
            if not name:
                logger.warning(
                    "ViewSaver: skipping savable %s with no objectName",
                    type(widget).__name__,
                )
                continue
            if name in self._excluded:
                continue
            prop_list = self._resolve_widget_props(widget)
            if prop_list:
                resolved[name] = prop_list
        return resolved

    def _resolve_widget_props(
        self,
        widget: QWidget,
    ) -> dict[str, tuple[Callable, Callable]] | None:
        """Resolve getter/setter callables for each persisted property of *widget*.

        widgets with ``get_view_saver_properties`` are resolved here; this is preferred.
        built-in widgets are checked in the widget registry (see ``registry.resolve_registry_props``).

        Returns a mapping ``{propKey: (getter, setter)}`` for the given widget
        instance, or ``None`` if no savable properties could be resolved.
        """
        if hasattr(widget, "get_view_saver_properties"):
            try:
                return widget.get_view_saver_properties()
            except Exception:
                logger.exception(f"ViewSaver: get_view_saver_properties failed for {type(widget).__name__}")
                return None
        return resolve_registry_props(widget)

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:  # noqa: N802
        """Save when the watched container window is closing."""
        if event.type() == QEvent.Close and self._loaded:
            logger.debug("Window close event fired, saving view to file.")
            self._save_settings()
        return super().eventFilter(obj, event)

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def sizeHint(self) -> QSize:  # noqa: N802
        """Default size when first dropped in Designer."""
        return QSize(200, 200)

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        """Draw a dashed outline and corner label, but only in Qt Designer.

        At runtime nothing is painted so the container is fully transparent and
        only its child widgets are visible.
        """
        if not is_qt_designer():
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Dashed border to mark the container bounds.
        pen = QPen(QColor(90, 130, 200))
        pen.setStyle(Qt.DashLine)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -2, -2), 4, 4)

        # Small corner label chip (kept out of the center so it never sits on
        # top of child widgets).
        font = QFont()
        font.setPointSize(7)
        painter.setFont(font)
        metrics = painter.fontMetrics()
        text = self._HINT_TEXT
        chip = QRect(2, 2, metrics.horizontalAdvance(text) + 8, metrics.height() + 2)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(90, 130, 200, 210))
        painter.drawRoundedRect(chip, 3, 3)
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(chip, Qt.AlignCenter, text)
        painter.end()

    def open_dialog(self) -> None:
        dialog = ViewSaverDialog(
            available_widgets=self._walk_widget_names(),
            excluded_widgets=list(self._excluded),
            dir_name=self._dir_name,
            file_name=self._file_name,
            parent=self,
        )
        if dialog.exec_():
            # set properties based on result
            dir_name, file_name, excluded = dialog.results()
            # informs designer the properties have changed for saves to ui file.
            update_property_for_widget(self, "dirName", dir_name)
            update_property_for_widget(self, "fileName", file_name)
            update_property_for_widget(self, "excludedWidgets", list(excluded))

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

    def _get_excluded_widgets(self) -> list[str]:
        return list(self._excluded)

    def _set_excluded_widgets(self, value: list[str]) -> None:
        self._excluded = list(value)

    excludedWidgets = Property("QStringList", _get_excluded_widgets, _set_excluded_widgets)
