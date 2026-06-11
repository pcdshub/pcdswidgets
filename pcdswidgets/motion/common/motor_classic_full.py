"""
Originally generated from jinja template ui_main_widget.j2

This file can be safely edited to change the runtime behavior of the widget.
"""

from pydm.utilities import ACTIVE_QT_WRAPPER, QtWrapperTypes
from qtpy.QtWidgets import QWidget

from pcdswidgets.builder.designer_options import DesignerOptions
from pcdswidgets.builder.icon_options import IconOptions
from pcdswidgets.generated.motion.common.motor_classic_full_base import MotorClassicFullBase

try:
    from qtpy.QtCore import pyqtProperty
except ImportError:
    from qtpy.QtCore import Property as pyqtProperty  # type: ignore

# Note: for forward compat, setting up enum properties is completely different
# depending on if we use pyqt5 or pyside6.
# I'm following the examples in PyDM here.
if ACTIVE_QT_WRAPPER == QtWrapperTypes.PYSIDE6:
    from enum import Enum

    from PySide6.QtCore import QEnum  # type: ignore

    @QEnum
    class MotorTypes(Enum):  # type: ignore
        """Options for motor type to select error reset PV."""

        GENERIC = 0
        IMS = 1
        BECKHOFF = 2
        BECKHOFF_LEGACY = 3

else:
    # pyqt5 can't use real python enums for this, unfortunately
    class MotorTypes:  # type: ignore
        """Options for motor type to select error reset PV."""

        GENERIC = 0
        IMS = 1
        BECKHOFF = 2
        BECKHOFF_LEGACY = 3


class MotorClassicFull(MotorClassicFullBase):
    """
    Generic motor widget at full size.

    This class is extended to allow us to support multiple
    types of motor IOCs with the same ui layout.

    The user can set the `motor_type` enum to change the
    following behavior:

    - Error reset PV and value

    There are four options:

    - GENERIC: default, no error reset.
    - IMS: standard IMS IOC (not motor record).
    - BECKHOFF: Motor that uses the 2026+ version of our TwinCAT motion libraries.
    - BECKHOFF_LEGACY: uses the pre-2026 version of the above.
    """

    designer_options = DesignerOptions(
        group="ECS Motion Common",
        is_container=False,
        icon=IconOptions.NONE,
    )
    # Boilerplate to make the enum property work
    if ACTIVE_QT_WRAPPER == QtWrapperTypes.PYQT5:
        from PyQt5.QtCore import Q_ENUM

        Q_ENUM(MotorTypes)
    MotorTypes = MotorTypes
    GENERIC = MotorTypes.GENERIC
    IMS = MotorTypes.IMS
    BECKHOFF = MotorTypes.BECKHOFF
    BECKHOFF_LEGACY = MotorTypes.BECKHOFF_LEGACY

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._motor_type = MotorTypes.GENERIC
        self._clear_error_suffix = ""
        self.PyDMPushButton_clear_error.hide()

    def after_set_macro(self, macro_name: str, value: str):
        """Puts motor prefix into error reset PV."""
        if macro_name == "MOTOR":
            self.new_clear_error_motor(value)

    def get_motor_type(self) -> MotorTypes | int:
        return self._motor_type

    def set_motor_type(self, value: MotorTypes | int) -> None:
        self._motor_type = value
        match value:
            case MotorTypes.IMS:
                self.new_clear_error_suffix(":SEQ_SELN")
                self.PyDMPushButton_clear_error.setPressValue(48)
                self.PyDMPushButton_clear_error.show()
            case MotorTypes.BECKHOFF:
                self.new_clear_error_suffix(":bReset")
                self.PyDMPushButton_clear_error.setPressValue(1)
                self.PyDMPushButton_clear_error.show()
            case MotorTypes.BECKHOFF_LEGACY:
                self.new_clear_error_suffix(":PLC:bReset")
                self.PyDMPushButton_clear_error.setPressValue(1)
                self.PyDMPushButton_clear_error.show()
            case _:
                self.PyDMPushButton_clear_error.hide()

    motor_type = pyqtProperty(MotorTypes, get_motor_type, set_motor_type)

    def new_clear_error_suffix(self, suffix: str):
        self._clear_error_suffix = suffix
        if motor := self.get_macro("MOTOR"):
            self.new_clear_error_motor(motor)

    def new_clear_error_motor(self, motor: str):
        if self._clear_error_suffix:
            self.PyDMPushButton_clear_error.set_channel(f"ca://{motor}{self._clear_error_suffix}")
