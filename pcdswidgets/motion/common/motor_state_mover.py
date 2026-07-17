"""
Originally generated from jinja template ui_main_widget.j2

This file can be safely edited to change the runtime behavior of the widget.
"""

from pathlib import Path

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
