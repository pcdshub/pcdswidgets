"""
PMPS variant of the motor state mover expert screen.

Wraps one :class:`MotorStateMoverExpandedPMPS` (plain mover on top + Normal tab,
and a Configuration tab holding the PMPS controls: arb_enable and maint_mode).

Required macros:
    MOTOR   base prefix, e.g. ``TST:D3`` (shared with the GET/SET widgets)
"""

from pydm import Display
from qtpy import QtWidgets

from pcdswidgets.motion.common.motor_state_mover_expanded import MotorStateMoverExpandedPMPS


class MotorStateMoverPMPSExpert(Display):
    def __init__(self, parent=None, args=None, macros=None):
        super().__init__(parent=parent, args=args, macros=macros)
        macros = macros or {}

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.expanded = MotorStateMoverExpandedPMPS()
        self.expanded.setProperty("motor", macros.get("MOTOR", ""))
        layout.addWidget(self.expanded)

    def ui_filename(self):
        # UI is built in __init__, so there is no .ui file to load.
        return None
