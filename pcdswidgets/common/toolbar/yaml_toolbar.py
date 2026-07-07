import logging
import os

import yaml
from pydm.widgets import PyDMRelatedDisplayButton, PyDMShellCommand
from qtpy import QtCore, QtWidgets
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QGridLayout, QPushButton

from pcdswidgets.common.dock.tab_dock_button import TabDockButton

logger = logging.getLogger(__name__)


class QuickAccessToolbar(QtWidgets.QWidget):
    """Tab Widget with tabs containing buttons defined via a yaml file"""

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self._tools_file = ""
        self._tools = None
        self._default_config = {"cols": 4}
        self.default_dock_button = None
        self._setup_ui()

    def set_tools_file(self, file: str):
        if not file:
            return
        self._tools_file = file
        with open(file) as tf:
            self._tools = yaml.full_load(tf)
        self._assemble_tabs()

    def _setup_ui(self):
        self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)

        main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(main_layout)
        self.tab = QtWidgets.QTabWidget()
        main_layout.addWidget(self.tab)

    def _assemble_tabs(self):
        if self._tools is None:
            return
        self.tab.clear()
        for tab_name, tab_params in self._tools.items():
            page = QtWidgets.QWidget()

            config = dict(self._default_config)
            config.update(tab_params.get("config", {}))

            cols = config.get("cols", 4)
            page.setLayout(SnakeLayout(cols))

            buttons = tab_params.get("buttons", {})
            for button_text, button_config in buttons.items():
                button_widget = self._button_factory(button_text, button_config)
                page.layout().addWidget(button_widget)

            def min_scroll_size_hint(*args, **kwargs):
                return QtCore.QSize(40, 40)

            scroll_area = QtWidgets.QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_area.setWidget(page)
            scroll_area.minimumSizeHint = min_scroll_size_hint
            self.tab.addTab(scroll_area, tab_name)

    def _button_factory(self, text, config):
        tp = config.pop("type")
        btn = QPushButton()
        if tp == "shell":
            btn = PyDMShellCommand()
            btn.showIcon = False
            btn.setText(text)
        elif tp == "display":
            btn = PyDMRelatedDisplayButton()
            btn.showIcon = False
            btn.setText(text)
        elif tp == "dock":
            btn = TabDockButton()
            btn.setText(text)
            if self.default_dock_button is None or config.pop("default", False):
                self.default_dock_button = btn

        for prop, val in config.items():
            if prop == "filename":
                if not os.path.isabs(val):
                    val = os.path.join(os.path.dirname(self._tools_file), val)
            try:
                setattr(btn, prop, val)
            except Exception as ex:
                logger.error(f"Failed to set property {prop} with value {val} for {tp}: {ex}")

        return btn


class SnakeLayout(QGridLayout):
    """
    Snaking Layout

    The size is the maximum number of widgets before beginning the next row or
    column. The direction specifies whether the grid pattern will be filled
    column first, or row first.

    Parameters
    ----------
    widgets: Iterable
        List of widgets to place in grid

    size: int
        Maximum size of row or column

    direction: Qt.Direction, optional
        Whether the layout is filled column or row first.

    Returns
    -------
    QGridLayout
        Filled with widgets provided in function call

    Example
    -------
    .. code:: python

        # Three rows
        gridify(widgets, 3, direction=Qt.Vertical)

        # Five columns
        gridify(widgets, 5, direction=Qt.Vertical)  # Default direction

    """

    def __init__(self, size, direction=Qt.Horizontal):
        super().__init__()
        self.size = int(size)
        self.direction = direction

    def addWidget(self, widget):  # type: ignore
        """Add a QWidget to the layout"""
        # Number of widgets already existing
        position = self.count()
        # Desired position based on current count
        grid_position = [position // self.size, position % self.size]
        # Start vertically if desired
        if self.direction == Qt.Vertical:
            grid_position.reverse()
        # Add to layout
        super().addWidget(widget, grid_position[0], grid_position[1])
