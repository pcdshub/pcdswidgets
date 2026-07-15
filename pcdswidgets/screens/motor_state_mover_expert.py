"""
Expert screen for the motor state mover (migration off Typhos).

Opened from the plain :class:`MotorStateMover` "Expert Screen" button. Wraps one
:class:`MotorStateMoverExpanded` (plain mover on top + Normal/Configuration tabs)
and configures it from the incoming macros.

Required macros:
    MOTOR        base prefix, e.g. ``TST:D3``
    STATE_COUNT  number of states (int), e.g. ``4``
    MOTOR_TOKENS comma-separated per-motor tokens, e.g. ``D1M1,D2M1,D3M1``
"""

from pydm import Display
from qtpy import QtWidgets

from pcdswidgets.motion.common.motor_state_mover_expanded import MotorStateMoverExpanded


class MotorStateMoverExpert(Display):
    def __init__(self, parent=None, args=None, macros=None):
        super().__init__(parent=parent, args=args, macros=macros)
        macros = macros or {}

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.expanded = MotorStateMoverExpanded()
        self.expanded.setProperty("motor", macros.get("MOTOR", ""))
        self.expanded.setProperty("motorTokens", macros.get("MOTOR_TOKENS", ""))
        try:
            self.expanded.setProperty("stateCount", int(macros.get("STATE_COUNT", 0)))
        except (TypeError, ValueError):
            self.expanded.setProperty("stateCount", 0)
        layout.addWidget(self.expanded)

    def ui_filename(self):
        # UI is built in __init__, so there is no .ui file to load.
        return None
