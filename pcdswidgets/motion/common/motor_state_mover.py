"""
Originally generated from jinja template ui_main_widget.j2

This file can be safely edited to change the runtime behavior of the widget.
"""

from pathlib import Path

from pydm.widgets.channel import PyDMChannel
from qtpy.QtCore import QTimer
from qtpy.QtWidgets import QWidget

from pcdswidgets.builder.designer_options import DesignerOptions
from pcdswidgets.builder.icon_options import IconOptions
from pcdswidgets.generated.motion.common.motor_state_mover_base import MotorStateMoverBase


class MotorStateMover(MotorStateMoverBase):
    designer_options = DesignerOptions(
        group="ECS Motion Common",
        is_container=False,
        icon=IconOptions.NONE,
    )

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        # Resolve the expert screen to an absolute path so the related-display
        # button finds it regardless of where the embedding display lives or
        # whether the screens dir is on PYDM_DISPLAYS_PATH. Mirrors the smaract
        # widgets' approach. The MOTOR macro is forwarded via the button's
        # templated `macros` property (see the .ui).
        expert = Path(__file__).parents[2] / "screens" / "motor_state_mover_expert.py"
        self.expertScreenButton.setFilenames([str(expert)])

        # Toggle the label under the moving LED between "moving" (busy set) and
        # "done" (busy clear), tracking STATE:BUSY_RBV. The MOTOR macro is not
        # available yet at construction time, so wait for it before connecting
        # (mirrors the smaract widgets' timer approach).
        self._busy_channel: PyDMChannel | None = None
        self._busy_timer = QTimer(parent=self)
        self._busy_timer.setInterval(100)
        self._busy_timer.setSingleShot(True)
        self._busy_timer.timeout.connect(self._setup_moving_label)
        self._busy_timer.start()

    def _setup_moving_label(self) -> None:
        """Connect the moving/done label once the MOTOR macro is populated."""
        motor = self._get_macro("MOTOR")
        if not motor:
            self._busy_timer.start()
            return
        self._busy_channel = PyDMChannel(
            address=f"ca://{motor}:STATE:BUSY_RBV",
            value_slot=self._update_moving_label,
        )
        self._busy_channel.connect()

    def _update_moving_label(self, value) -> None:
        self.movingIndicatorLabel.setText("moving" if value else "done")
