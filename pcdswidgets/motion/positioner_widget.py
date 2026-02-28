from pydm.widgets.qtplugins import ifont

from pcdswidgets.builder.ui.positioner_base import PositionerWidgetBase


class PositionerWidget(PositionerWidgetBase):
    _qt_designer_ = {
        "group": "PCDS Motion",
        "is_container": False,
        "icon": ifont.icon("expand-arrows-alt"),
    }
