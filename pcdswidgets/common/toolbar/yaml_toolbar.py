"""
A button toolbar loaded from a lucid-style yaml file.

This was originally part of lucid but has moved here so it can be used without
the lucid launcher, of which it has no real dependencies.
"""

import logging
import os
from typing import Any

import yaml
from pydm.widgets import PyDMRelatedDisplayButton, PyDMShellCommand
from qtpy import QtCore, QtWidgets
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QGridLayout, QPushButton, QWidget

from pcdswidgets.common.dock.tab_dock_button import TabDockButton

try:
    from qtpy.QtCore import Property  # type: ignore
except ImportError:
    from qtpy.QtCore import pyqtProperty as Property  # type: ignore

logger = logging.getLogger(__name__)


class YamlToolbar(QtWidgets.QWidget):
    """
    Tab Widget with tabs containing buttons defined via a yaml file.

    This uses the legacy yaml format from lucid, which defines which buttons go in which tab.

    See https://pcdshub.github.io/lucid/master/toolbar.html for more information.
    """

    _qt_designer_ = {
        "group": "ECS Common Toolbar",
        "is_container": False,
    }

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent=parent)

        self._config_file = ""
        self._default_config = {"cols": 4}
        self.default_dock_button = None

        self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(main_layout)
        self.tab = QtWidgets.QTabWidget()
        main_layout.addWidget(self.tab)

    def get_config_file(self) -> str:
        """Return the last set path to the toolbar config yaml file."""
        return self._config_file

    def set_config_file(self, file: str):
        """
        Set the path to the toolbar config yaml file and create the necessary tabs and buttons.

        Parameters
        ----------
        file : str
            The absolute path to the config file.
        """
        if not file:
            return
        if not os.path.isfile(file):
            return
        self._config_file = file
        with open(file) as tf:
            full_config = yaml.full_load(tf)
        self._assemble_tabs(full_config)

    filename = Property("QString", get_config_file, set_config_file)

    def _assemble_tabs(self, full_config: dict[str, dict[str, Any]]):
        """
        Build the tabs from the user's yaml config.

        Parameters
        ----------
        full_config : dict
            The serialized configuration from the user's yaml file.
            Contains configuration information for all tabs.
        """
        self.tab.clear()
        for tab_name, tab_params in full_config.items():
            page = QtWidgets.QWidget()

            config = dict(self._default_config)
            config.update(tab_params.get("config", {}))

            cols = config.get("cols", 4)
            page.setLayout(YamlTabLayout(cols))

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

    def _button_factory(self, text: str, config: dict[str, Any]) -> QPushButton:
        """
        Create and return a single button for the grid.

        Parameters
        ----------
        text : str
            The text to put on the button.
        config : dict[str, str]
            The configuration for this button as specified in the yaml file.
            This is a dictionary mapping with one special key, "type" that
            is the button type to use. The valid types are "shell",
            "display", "dock". All other key/value pairs are property/value
            pairs to set on the button instance.
        """
        tp = config.pop("type")
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
        else:
            raise RuntimeError(f"Invalid button type {tp}")

        for prop, val in config.items():
            if prop == "filename":
                if not os.path.isabs(val):
                    val = os.path.join(os.path.dirname(self._config_file), val)
            try:
                setattr(btn, prop, val)
            except Exception as ex:
                logger.error(f"Failed to set property {prop} with value {val} for {tp}: {ex}")

        return btn


class YamlTabLayout(QGridLayout):
    """
    QGridLayout with a simplified addWidget function.

    The size is the maximum number of widgets before beginning the next row or
    column. The direction specifies whether the grid pattern will be filled
    column first, or row first.

    Parameters
    ----------
    size: int
        Maximum size of row or column

    direction: Qt.Orientation, optional
        Whether the layout is filled column or row first.
    """

    def __init__(self, size: int, direction: Qt.Orientation = Qt.Horizontal):
        super().__init__()
        self.size = int(size)
        self.direction = direction

    def addWidget(self, widget: QWidget):  # type: ignore
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
