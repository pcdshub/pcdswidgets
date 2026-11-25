"""A PyDMEnumComboBox that asks before it writes, for the ``common.ethercat`` widgets."""

from __future__ import annotations

from collections.abc import Callable

from pydm.widgets.enum_combo_box import PyDMEnumComboBox
from qtpy.QtCore import Slot


class ConfirmingEnumComboBox(PyDMEnumComboBox):
    """
    A :class:`PyDMEnumComboBox` that writes only what its ``confirm`` hook accepts.

    ``confirm(index) -> bool`` is called when the user picks an item: the value is
    written if it returns True, otherwise the selection goes back to the last value
    of the channel. Without ``confirm`` it behaves exactly like PyDMEnumComboBox.
    Used in .ui files as a promoted PyDMEnumComboBox.
    """

    def __init__(self, parent=None, init_channel=None):
        super().__init__(parent, init_channel)
        self.confirm: Callable[[int], bool] | None = None

    @Slot(int)
    def internal_combo_box_activated_int(self, index: int):
        if self.confirm is not None and not self.confirm(index):
            self.setCurrentIndex(int(self.value) if self.value is not None else -1)
            return
        super().internal_combo_box_activated_int(index)
