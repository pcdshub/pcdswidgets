"""Module for IpmFull"""
# Originally generated from jinja template ui_main_widget.j2
# This file can be safely edited to change the runtime behavior of the widget.

from pcdswidgets.builder.designer_options import DesignerOptions
from pcdswidgets.builder.icon_options import IconOptions
from pcdswidgets.generated.common.beam_diagnostics.ipm_full_base import IpmFullBase


class IpmFull(IpmFullBase):
    designer_options = DesignerOptions(
        group="ECS Common Beam_Diagnostics",
        is_container=False,
        icon=IconOptions.NONE,
    )
