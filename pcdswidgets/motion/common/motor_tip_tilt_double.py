"""
Originally generated from jinja template ui_main_widget.j2

This file can be safely edited to change the runtime behavior of the widget.
"""

import logging

from pydm.widgets import PyDMPushButton, PyDMShellCommand
from qtpy.QtWidgets import QCheckBox, QWidget

from pcdswidgets.builder.designer_options import DesignerOptions
from pcdswidgets.builder.icon_options import IconOptions
from pcdswidgets.generated.motion.common.motor_tip_tilt_double_base import MotorTipTiltDoubleBase

logger = logging.getLogger(__name__)


class MotorTipTiltDouble(MotorTipTiltDoubleBase):
    # some type hinting
    vertical_invert: QCheckBox
    horizontal_invert: QCheckBox
    step_up: PyDMPushButton
    step_down: PyDMPushButton
    step_left: PyDMPushButton
    step_right: PyDMPushButton
    vertical_expert_screen: PyDMShellCommand
    horizontal_expert_screen: PyDMShellCommand

    designer_options = DesignerOptions(
        group="ECS Motion Common",
        is_container=False,
        icon=IconOptions.NONE,
    )

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.vertical_invert.stateChanged.connect(self._invert_vertical)
        self.horizontal_invert.stateChanged.connect(self._invert_horizontal)
    
    def _invert_axis_channel(self, axis: str) -> None:
        """
        Invert the TWF or TWR channel connections for a particular
        axis in the directional pad

        Parameters
        ----------
        axis : str
            One of ['vertical', 'horizontal']
        """
        checkbox: QCheckBox
        widget: PyDMPushButton

        if axis not in ["vertical", "horizontal"]:
            # Don't be silly please
            return

        motor_pv = self.get_macro(f"{axis}_motor")

        if not motor_pv:
            logger.debug(f"Macro for {axis}_motor does not yet exist")
            return

        checkbox = getattr(self, f"{axis}_invert")
        directions = ["up", "down"] if axis == "vertical" else ["right", "left"]

        # didn't want to use dir/s as an iterator which is normally for directory
        for d in directions:
            if d in ["up", "right"]:
                pv_suffix = "TWR" if checkbox.isChecked() else "TWF"
            else:
                pv_suffix = "TWF" if checkbox.isChecked() else "TWR"
            widget = getattr(self, f"step_{d}")
            widget.set_channel(f"ca://{motor_pv}.{pv_suffix}")

    def set_motors(self, horizontal_motor: str, vertical_motor: str) -> None:
        """
        Reassign which motor PVs drive the horizontal and vertical axes.

        Parameters
        ----------
        horizontal_motor : str
            PV to assign to the horizontal axis.
        vertical_motor : str
            PV to assign to the vertical axis.
        """
        self.set_macro("horizontal_motor", horizontal_motor)
        self.set_macro("vertical_motor", vertical_motor)
        self._invert_axis_channel("horizontal")
        self._invert_axis_channel("vertical")

    def _invert_vertical(self) -> None:
        """Swap the TWF and TWR buttons for the vertical axis"""
        self._invert_axis_channel("vertical")

    def _invert_horizontal(self) -> None:
        """Swap the TWF and TWR buttons for the horizontal axis"""
        self._invert_axis_channel("horizontal")
    
