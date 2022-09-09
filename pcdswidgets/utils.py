import logging

from qtpy.QtWidgets import QWidget

logger = logging.getLogger(__name__)


def refresh_style(widget):
    """
    Method that traverse the widget tree starting at `widget` and refresh the
    style for this widget and its childs.

    Parameters
    ----------
    widget : QWidget
    """
    widgets = [widget]
    widgets.extend(widget.findChildren(QWidget))
    for child_widget in widgets:
        child_widget.style().unpolish(child_widget)
        child_widget.style().polish(child_widget)
        child_widget.update()
        if child_widget != widget:
            refresh_style(child_widget)


def find_ancestor_for_widget(widget, klass):
    w = widget
    while w.parent() is not None:
        w = w.parent()
        if isinstance(w, klass):
            return w
    return None
