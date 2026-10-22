"""Overridden combo box widgets.

Ignore wheel events unless the combo box has keyboard focus
"""

from qtpy.QtWidgets import QComboBox

from .pcds_spinbox import NoScrollMixin


class NoScrollComboBox(NoScrollMixin, QComboBox):
    """regular ``QComboBox`` that ignores wheel events unless focused."""


# PyDMCombobox already does not react to scroll events.
