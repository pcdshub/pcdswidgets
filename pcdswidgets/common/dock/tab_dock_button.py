"""A simple push button to open pydm screens in the TabDock widget."""

from typing import cast

from pydm.display import ScreenTarget, clear_compiled_ui_file_cache, load_file
from pydm.utilities import IconFont, find_file
from pydm.utilities.macro import parse_macro_string
from pydm.utilities.stylesheet import merge_widget_stylesheet
from qtpy.QtGui import QContextMenuEvent, QCursor
from qtpy.QtWidgets import (
    QPushButton,
    QWidget,
)

from .tab_dock import TabDock

try:
    from qtpy.QtCore import Property  # type: ignore
except ImportError:
    from qtpy.QtCore import pyqtProperty as Property  # type: ignore


ifont = IconFont()


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

    _qt_designer_ = {
        "group": "ECS Common Dock",
        "is_container": False,
    }

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._filename: str = ""
        self._macro: str = ""
        self.clicked.connect(self.open_in_dock)
        self._icon = ifont.icon("anchor")
        self.setCursor(QCursor(self._icon.pixmap(16, 16)))  # type: ignore
        self.cached_ui_text = ""
        self.cached_widget: QWidget | None = None

    def build_widget(self) -> QWidget:
        """Create or re-use the widget defined by the pydm file."""
        fname = find_file(
            self._filename,
            raise_if_not_found=True,
        )
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

    def open_in_dock(self):
        """Place the widget defined by this button into the dock based on the key modifiers."""
        TabDock.add_to_dock_user_keybinds(widget=self.build_widget)

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:  # type: ignore
        """On right-click, open a menu to decide where the widget should go."""
        TabDock.add_to_dock_user_menu(widget=self.build_widget, pos=event.globalPos())

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
