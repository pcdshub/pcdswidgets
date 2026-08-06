"""Shared PyDM widgets for the motor state mover screens."""

from pydm.widgets.label import PyDMLabel


class MovingLabel(PyDMLabel):
    """Label under the moving LED: shows "moving" when the tracked value
    (STATE:BUSY_RBV) is set, "done" when it is clear."""

    def value_changed(self, value) -> None:
        try:
            busy = bool(int(value))
        except (TypeError, ValueError):
            busy = bool(value)
        self.setText("moving" if busy else "done")
