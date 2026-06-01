"""
Originally generated from jinja template ui_main_widget.j2

This file can be safely edited to change the runtime behavior of the widget.
"""

from pcdswidgets.builder.designer_options import DesignerOptions
from pcdswidgets.builder.icon_options import IconOptions
from pcdswidgets.generated.imaging.common.marker_selection_full_base import MarkerSelectionFullBase


class MarkerSelectionFull(MarkerSelectionFullBase):
    designer_options = DesignerOptions(
        group="ECS Imaging Common",
        is_container=False,
        icon=IconOptions.NONE,
    )
