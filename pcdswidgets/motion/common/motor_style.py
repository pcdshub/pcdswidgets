"""
Defines the MotorStyle enum.

Controls whether a tip/tilt widget drives its axes using the standard EPICS
motor record fields (TWF/TWR/TWV/RBV) or the SmarAct MCS2 controller's
non-standard step fields (STEP_FORWARD/STEP_REVERSE/STEP_COUNT/TOTAL_STEP_COUNT).
"""

from enum import StrEnum


class MotorStyle(StrEnum):
    MOTOR_RECORD = "motor_record"
    SMARACT = "smaract"
