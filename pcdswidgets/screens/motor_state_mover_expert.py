"""
Expert screen for the motor state mover (migration off Typhos).

Opened from the plain :class:`MotorStateMover` "Expert Screen" button. Wraps one
:class:`MotorStateMoverExpanded` (plain mover on top + Normal/Configuration tabs)
and configures it from the incoming macros.

Macros:
    DEVICE       base prefix, e.g. ``TST:D3`` (required)
    PMPS         truthy ("1"/"true") -> PMPS variant: the Configuration tab adds
                 the PMPS controls (arb_enable, maint_mode) above the per-state
                 motor grid.
    STATE_COUNT  number of states (int), e.g. ``4``
    DEVICE_TOKENS comma-separated per-device tokens, e.g. ``D1M1,D2M1,D3M1``
"""

from pydm import Display
from qtpy import QtWidgets

from pcdswidgets.motion.common.motor_state_mover_expanded import (
    MotorStateMoverExpanded,
    MotorStateMoverExpandedPMPS,
)

_TRUTHY = {"1", "true", "yes", "on"}


class MotorStateMoverExpert(Display):
    def __init__(self, parent=None, args=None, macros=None):
        super().__init__(parent=parent, args=args, macros=macros)
        macros = macros or {}

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        if str(macros.get("PMPS", "")).strip().lower() in _TRUTHY:
            self.expanded = MotorStateMoverExpandedPMPS()
        else:
            self.expanded = MotorStateMoverExpanded()

        # both variants use the per-state grid (the PMPS one shows it below its
        # arb_enable / maint_mode controls), so feed all three to either widget
        self.expanded.setProperty("device", macros.get("DEVICE", ""))
        self.expanded.setProperty("deviceTokens", macros.get("DEVICE_TOKENS", ""))
        try:
            self.expanded.setProperty("stateCount", int(macros.get("STATE_COUNT", 0)))
        except (TypeError, ValueError):
            self.expanded.setProperty("stateCount", 0)

        layout.addWidget(self.expanded)

    def ui_filename(self):
        # UI is built in __init__, so there is no .ui file to load.
        return None
