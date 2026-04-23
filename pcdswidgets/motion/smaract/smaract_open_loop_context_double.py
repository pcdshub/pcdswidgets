"""
Originally generated from jinja template ui_main_widget.j2

This file can be safely edited to change the runtime behavior of the widget.
"""

import logging

from pydm import Display
from pydm.widgets import PyDMPushButton
from qtpy.QtWidgets import QWidget

from pcdswidgets.builder.designer_options import DesignerOptions
from pcdswidgets.builder.icon_options import IconOptions
from pcdswidgets.generated.motion.smaract.smaract_open_loop_context_double_base import SmaractOpenLoopContextDoubleBase

logger = logging.getLogger(__name__)


class SmaractOpenLoopContextDouble(SmaractOpenLoopContextDoubleBase):
    clear_step_count: PyDMPushButton

    designer_options = DesignerOptions(
        group="ECS Motion Smaract",
        is_container=False,
        icon=IconOptions.NONE,
    )


class SmarActOpenLoopContextDoubleDisplay(SmaractOpenLoopContextDouble, Display):
    """This widget is intended to be opened with a PyDMRelatedDisplayButton"""

    def __init__(self, parent: QWidget | None = None, args=None, macros=None):
        # Initialize Display FIRST with macros, mro is mean
        Display.__init__(self, parent=parent, args=args, macros=macros)
        # Then initialize DesignerWidget
        SmaractOpenLoopContextDouble.__init__(self, parent=parent)

        # Sync Display's macros into DesignerWidget's macro system
        # Otherwise PyDMRelatedDisplayButtons will not pass their macros
        if macros:
            for key, value in macros.items():
                self._set_macro(key, value)
