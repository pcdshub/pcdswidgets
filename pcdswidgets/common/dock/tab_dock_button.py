"""A simple push button to open pydm screens in the TabDock widget."""

from enum import IntEnum
from typing import cast

from pydm.display import ScreenTarget, clear_compiled_ui_file_cache, load_file
from pydm.utilities import IconFont, find_file
from pydm.utilities.macro import parse_macro_string
from pydm.utilities.stylesheet import merge_widget_stylesheet

from qtpy.QtCore import Q_ENUMS
from qtpy.QtGui import QContextMenuEvent, QCursor, QEnterEvent
from qtpy.QtWidgets import (
    QPushButton,
    QWidget,
)

from pcdswidgets.show_screen import get_screen_path, get_widget_type

from .tab_dock import NoTabDockError, TabDock

try:
    from qtpy.QtCore import Property  # type: ignore
except ImportError:
    from qtpy.QtCore import pyqtProperty as Property  # type: ignore


ifont = IconFont()


class ScreenSource(IntEnum):
    """Options for how we should interpret the filename and macro properties."""

    FILE_PATH = 0
    SCREEN_NAME = 1
    WIDGET_NAME = 2


class TabDockButton(QPushButton):
    """
    A QPushButton that opens a PyDM screen in the TabDock when clicked.

    The user must set the "filename" property to the path of the screen to use,
    and may optionally set the "macro" property to the macro string used
    to substitute values into the fields.

    Parameters
    ----------
    parent : QWidget, optional
        Standard qt parent argument
    """

    Q_ENUMS(ScreenSource)
    ScreenSource = ScreenSource
    FILE_PATH = ScreenSource.FILE_PATH
    SCREEN_NAME = ScreenSource.SCREEN_NAME
    WIDGET_NAME = ScreenSource.WIDGET_NAME

    _qt_designer_ = {
        "group": "ECS Common Dock",
        "is_container": False,
    }

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._filename: str = ""
        self._macro: str = ""
        self.clicked.connect(self.open_in_dock)
        self.cached_ui_text = ""
        self.cached_widget: QWidget | None = None
        self._source = ScreenSource.FILE_PATH
        self._finalized_mouseover_icon = False

    def build_widget(self) -> QWidget:
        """Create the widget and return it, or re-use an existing widget if possible."""
        if self._source == ScreenSource.FILE_PATH:
            return self.build_widget_from_filepath(is_screen_name=False)
        if self._source == ScreenSource.SCREEN_NAME:
            return self.build_widget_from_filepath(is_screen_name=True)
        if self._source == ScreenSource.WIDGET_NAME:
            return self.build_widget_from_widget_name()
        raise ValueError(f"Invalid option {self._source} for screen source.")

    def build_widget_from_filepath(self, is_screen_name: bool) -> QWidget:
        """Create or re-use the widget defined by the pydm file."""
        if is_screen_name:
            fname = get_screen_path(self._filename)
        else:
            try:
                fname = find_file(
                    self._filename,
                    raise_if_not_found=True,
                )
            except FileNotFoundError as exc:
                raise ValueError(
                    f"In button named {self.objectName()}, unable to find filename '{self.readFilename()}'"
                ) from exc
            fname = cast(str, fname)

        macros = parse_macro_string(self._macro)
        with open(fname, "r") as fd:
            ui_text = fd.read()

        if ui_text != self.cached_ui_text or self.cached_widget is None:
            if self.cached_widget is not None:
                clear_compiled_ui_file_cache()
                self.cached_widget.close()
            display = cast(QWidget, load_file(fname, macros=macros, target=ScreenTarget.DIALOG))
            display.hide()
            merge_widget_stylesheet(widget=display)
            self.cached_ui_text = ui_text
            self.cached_widget = display
        else:
            display = self.cached_widget
        return display

    def build_widget_from_widget_name(self) -> QWidget:
        """Create the named widget from pcdswidgets."""
        ui_text = self._filename + self._macro
        if ui_text != self.cached_ui_text or self.cached_widget is None:
            if self.cached_widget is not None:
                self.cached_widget.close()
            WidgetType = get_widget_type(widget=self._filename)
            widget = WidgetType()
            props = parse_macro_string(self._macro)
            for key, value in props.items():
                widget.setProperty(key, value)
            self.cached_ui_text = ui_text
            self.cached_widget = widget
        else:
            widget = self.cached_widget
        return widget

    def open_in_dock(self):
        """Place the widget defined by this button into the dock based on the key modifiers."""
        try:
            TabDock.add_to_dock_user_keybinds(widget=self.build_widget)
        except NoTabDockError:
            self.open_window_fallback()

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:  # type: ignore
        """On right-click, open a menu to decide where the widget should go."""
        try:
            TabDock.add_to_dock_user_menu(widget=self.build_widget, pos=event.globalPos())
        except NoTabDockError:
            self.open_window_fallback()

    def open_window_fallback(self) -> None:
        """If there is no tab dock, open a simple window."""
        widget = self.build_widget()
        TabDock.show_widget_at_cursor(widget)

    def enterEvent(self, event: QEnterEvent) -> None:  # type: ignore
        if not self._finalized_mouseover_icon:
            try:
                TabDock.get_instance()
            except NoTabDockError:
                self._icon = ifont.icon("file")
                self.setCursor(QCursor(self._icon.pixmap(16, 16)))  # type: ignore
            else:
                self._icon = ifont.icon("anchor")
                self.setCursor(QCursor(self._icon.pixmap(16, 16)))  # type: ignore
            self._finalized_mouseover_icon = True
        return super().enterEvent(event)

    def readFilename(self) -> str:
        return self._filename

    def setFilename(self, val: str) -> None:
        self._filename = val

    filename = Property("QString", readFilename, setFilename)

    def readMacro(self) -> str:
        return self._macro

    def setMacro(self, new_macro: str) -> None:
        self._macro = new_macro

    macros = Property("QString", readMacro, setMacro)

    def readSource(self) -> ScreenSource:
        return self._source

    def setSource(self, source: ScreenSource) -> None:
        self._source = source

    source = Property(ScreenSource, readSource, setSource)
