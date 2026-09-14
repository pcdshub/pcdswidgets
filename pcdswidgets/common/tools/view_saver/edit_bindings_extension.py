"""Designer task-menu extension for editing ViewSaver settings."""

from __future__ import annotations

from qtpy.QtWidgets import QAction

from .registry import discover_widgets
from .view_saver_dialog import ViewSaverDialog


class EditWidgetListExtension:
    """Adds an 'Edit ViewSaver…' action to the Designer right-click menu.

    Follows the same pattern as ``MacroEditExtension`` in
    ``pcdswidgets.builder.designer_widget``.  PyDM instantiates this class
    with the widget and calls :meth:`actions` for the task-menu entries.
    The first action is also mapped to double-click.
    """

    def __init__(self, widget):
        self.widget = widget
        self._action = QAction("&Edit ViewSaver\u2026", self.widget)
        self._action.triggered.connect(self._open_dialog)

    def actions(self) -> list[QAction]:
        return [self._action]

    def _open_dialog(self) -> None:
        from pydm.widgets.designer_settings import update_property_for_widget

        widget = self.widget
        dialog = ViewSaverDialog(
            available_widgets=discover_widgets(widget.window()),
            existing_widgets=list(widget._tracked_widgets.keys()),
            dir_name=widget._dir_name,
            file_name=widget._file_name,
            parent=widget,
        )
        if dialog.exec_():
            dir_name, file_name, widget_names = dialog.results()
            widget.dirName = dir_name
            widget.fileName = file_name
            widget.widget_names = widget_names
            update_property_for_widget(widget, "dirName", widget._dir_name)
            update_property_for_widget(widget, "fileName", widget._file_name)
            update_property_for_widget(
                widget, "widget_names", list(widget._tracked_widgets.keys())
            )
