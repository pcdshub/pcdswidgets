"""
Originally generated from jinja template ui_main_widget.j2

This file can be safely edited to change the runtime behavior of the widget.
"""

import json
import logging
from pathlib import Path

from pydm.widgets import PyDMPushButton, PyDMRelatedDisplayButton
from qtpy.QtCore import QTimer
from qtpy.QtGui import QIcon
from qtpy.QtWidgets import QCheckBox, QWidget

from pcdswidgets.builder.designer_options import DesignerOptions
from pcdswidgets.builder.icon_options import IconOptions
from pcdswidgets.generated.motion.smaract.smaract_tip_tilt_double_base import SmaractTipTiltDoubleBase

logger = logging.getLogger(__name__)


class SmaractTipTiltDouble(SmaractTipTiltDoubleBase):
    # some type hinting
    vertical_invert: QCheckBox
    horizontal_invert: QCheckBox
    step_up: PyDMPushButton
    step_down: PyDMPushButton
    step_left: PyDMPushButton
    step_right: PyDMPushButton
    vertical_expert_screen: PyDMRelatedDisplayButton
    horizontal_expert_screen: PyDMRelatedDisplayButton

    designer_options = DesignerOptions(
        group="ECS Motion Smaract",
        is_container=False,
        icon=IconOptions.NONE,
    )

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.vertical_invert.stateChanged.connect(self._invert_vertical)
        self.horizontal_invert.stateChanged.connect(self._invert_horizontal)
        # For now, we will link the expert screens for tip-tilts
        # to a limited context window
        self._macros_timer = QTimer(parent=self)
        self._macros_timer.timeout.connect(self._setup_expert_screens)
        self._macros_timer.setInterval(100)
        self._macros_timer.setSingleShot(True)
        self._macros_timer.start()

    @staticmethod
    def get_designer_icon() -> str:
        """Icon for usage in Qt designer."""
        return QIcon(str(Path(__file__).parent / "smaract_tip_tilt_qt_icon.png"))

    def _setup_expert_screens(self):
        """Macros aren't immediately available through _get_macros, wait until they are."""
        if not self._get_macro("vertical_motor") or not self._get_macro("horizontal_motor"):
            self._macros_timer.start()
            return

        self._set_expert_screen_macro("vertical")
        self._set_expert_screen_macro("horizontal")

    def _set_expert_screen_macro(self, axis: str) -> None:
        """
        Explicitly set the macros for the PyDMRelatedDisplay as a JSON digestible str

        Parameters
        ----------
        axis : str
            One of ['vertical', 'horizontal']
        """
        motor_pv: str
        button: PyDMRelatedDisplayButton

        if axis not in ["vertical", "horizontal"]:
            # Don't be silly, silly
            return

        motor_pv = self._get_macro(f"{axis}_motor")

        if not motor_pv:
            logger.debug(f"Macro for {axis}_motor does not yet exist")
            return

        button = getattr(self, f"{axis}_expert_screen")

        button.setFilenames([str(Path(__file__).parents[1] / "ui/motion/smaract/smaract_open_loop_context.ui")])
        logger.debug(f"Setting {axis} expert screen filename to {button.filenames}()")

        button.setMacros(json.dumps({"motor": motor_pv}))
        logger.debug(f"Setting {axis} expert screen with macros {button._macros}")

    def _invert_axis_channel(self, axis: str) -> None:
        """
        Invert the STEP_FORWARD or STEP_REVERSE channel connections for a particular
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

        motor_pv = self._get_macro(f"{axis}_motor")

        if not motor_pv:
            logger.debug(f"Macro for {axis}_motor does not yet exist")
            return

        checkbox = getattr(self, f"{axis}_invert")
        directions = ["up", "down"] if axis == "vertical" else ["right", "left"]

        # didn't want to use dir/s as an iterator which is normally for directory
        for d in directions:
            if d in ["up", "right"]:
                pv_suffix = "REVERSE" if checkbox.isChecked() else "FORWARD"
            else:
                pv_suffix = "FORWARD" if checkbox.isChecked() else "REVERSE"
            widget = getattr(self, f"step_{d}")
            widget.set_channel(f"ca://{motor_pv}:STEP_{pv_suffix}.PROC")

    def _invert_vertical(self) -> None:
        """Swap the FWD and BWD buttons for the vertical axis"""
        self._invert_axis_channel("vertical")

    def _invert_horizontal(self) -> None:
        """Swap the FWD and BWD buttons for the horizontal axis"""
        self._invert_axis_channel("horizontal")
