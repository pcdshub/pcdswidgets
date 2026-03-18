from pydm.widgets.qtplugins import ifont

from pcdswidgets.builder.ui.smaract_open_loop_full_base import SmaractOpenLoopFullBase


class SmaractOpenLoopFull(SmaractOpenLoopFullBase):
    _qt_designer_ = {
        "group": "PCDS Motion",
        "is_container": False,
        "icon": ifont.icon("arrows-alt-h"),
    }
