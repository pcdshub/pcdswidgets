"""override default signal/slot behavior of the spinbox"""

from pydm.widgets import PyDMSpinbox
from qtpy.QtCore import Qt


class PyDMSpinboxEnter(PyDMSpinbox):
    """Overrides for PyDMSpinbox for handling editing events"""

    def __init__(self, parent=None, init_channel=None):
        super().__init__(parent, init_channel)

    def keyPressEvent(self, ev):
        """
        The default <Enter> press event does not validate text if
        keyboardTracking is off causing a stale value to be sent.

        Also want focus clear after a new value is set.
        """
        if ev.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.interpretText()
            self.send_value()
            self.clearFocus()
        else:
            super().keyPressEvent(ev)
