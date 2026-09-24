"""Assorted utility helpers shared across pcdswidgets."""

import logging

from qtpy.QtWidgets import QWidget

logger = logging.getLogger(__name__)


def refresh_style(widget):
    """
    Refresh the widget's stylesheet and every descendant widget's stylesheet.

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
    """Return the nearest ancestor of ``widget`` that is an instance of ``klass``."""
    w = widget
    while w.parent() is not None:
        w = w.parent()
        if isinstance(w, klass):
            return w
    return None
