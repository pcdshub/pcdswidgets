from pydm.widgets.qtplugins import ifont

from pcdswidgets.builder.ui.smaract_open_loop_base import SmaractOpenLoopWidgetBase


class SmaractOpenLoopWidget(SmaractOpenLoopWidgetBase):
    _qt_designer_ = {
        "group": "PCDS Motion",
        "is_container": False,
        "icon": ifont.icon("arrows-alt-h"),
    }
