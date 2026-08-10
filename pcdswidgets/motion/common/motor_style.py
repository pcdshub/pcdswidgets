"""
Defines the MotorStyle enum.

Controls whether a tip/tilt widget drives its axes using the standard EPICS
motor record fields (TWF/TWR/TWV/RBV) or the SmarAct MCS2 controller's
non-standard step fields (STEP_FORWARD/STEP_REVERSE/STEP_COUNT/TOTAL_STEP_COUNT).
"""

from enum import IntEnum


class MotorStyle(IntEnum):
    """
    Designer-visible enum for motor_style. PyQt5-only: each widget class
    registers this via Q_ENUMS for a Designer dropdown; PySide6 needs a real
    enum.Enum decorated with @QEnum instead, so this exact pattern isn't portable.
    """

    MotorRecord = 0
    Smaract = 1
