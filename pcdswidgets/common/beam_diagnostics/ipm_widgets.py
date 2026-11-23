"""
Custom PyDM widgets for the compact IPM screen.

ThrottledPyDMLabel: a PyDMLabel that rate-limits how often it repaints, without
touching the PV or its .SCAN field. The underlying channel still monitors at full
speed (e.g. the wave8 :SUM at ~120 Hz); this widget only coalesces those updates to
a fixed display rate so the number stays readable. Alarm color, units, and precision
all keep working because it remains a PyDMLabel.
"""

from pydm.widgets import PyDMLabel
from qtpy.QtCore import Property, QTimer


class ThrottledPyDMLabel(PyDMLabel):
    """A PyDMLabel whose displayed value updates at most ``throttleRate`` times/sec."""

    def __init__(self, parent=None, init_channel=None):
        super().__init__(parent=parent, init_channel=init_channel)
        self._throttle_rate = 5.0  # Hz
        self._pending = None
        self._has_pending = False
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._flush)
        self._start_timer()

    def _start_timer(self):
        if self._throttle_rate > 0:
            self._timer.setInterval(int(1000.0 / self._throttle_rate))
            self._timer.start()
        else:
            self._timer.stop()

    def _flush(self):
        """Push the most recent pending value to the real PyDMLabel, if any."""
        if self._has_pending:
            self._has_pending = False
            pending, self._pending = self._pending, None
            super().value_changed(pending)

    def value_changed(self, new_value):
        """Store the latest value; the timer emits it at the throttled rate."""
        # Keep PyDMLabel's internal bookkeeping (self.value, format handling) current
        # without repainting on every callback: stash the value and defer the setText.
        self.value = new_value
        self._pending = new_value
        self._has_pending = True

    @Property(float)
    def throttleRate(self):
        """Maximum display refresh rate, in Hz (0 disables throttling)."""
        return self._throttle_rate

    @throttleRate.setter
    def throttleRate(self, rate):
        self._throttle_rate = float(rate)
        self._start_timer()
