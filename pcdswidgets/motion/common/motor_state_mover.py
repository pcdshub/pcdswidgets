"""
Originally generated from jinja template ui_main_widget.j2

This file can be safely edited to change the runtime behavior of the widget.
"""

from pcdswidgets.builder.designer_options import DesignerOptions
from pcdswidgets.builder.icon_options import IconOptions
from pcdswidgets.generated.motion.common.motor_state_mover_base import MotorStateMoverBase


class MotorStateMover(MotorStateMoverBase):
    designer_options = DesignerOptions(
        group="ECS Motion Common",
        is_container=False,
        icon=IconOptions.NONE,
    )
    # The expert-screen button's filename is a package-relative path
    # (pcdswidgets/motion/common/motor_state_mover_expert.py); DesignerWidget's
    # update_relative_paths() resolves it to the absolute install path at load.
    # The moving/done label (movingIndicatorLabel) is a promoted MovingLabel
    # bound to STATE:BUSY_RBV in the .ui, so both work with no runtime setup.
