from pydm.widgets.qtplugins import ifont

from pcdswidgets.builder.ui.positioner_row_base import PositionerRowWidgetBase


class PositionerRowWidget(PositionerRowWidgetBase):
    _qt_designer_ = {
        "group": "PCDS Motion",
        "is_container": False,
        "icon": ifont.icon("arrows-alt-h"),
    }
