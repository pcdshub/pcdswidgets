from pcdswidgets.builder.ui.positioner_base import PositionerWidgetBase
from pcdswidgets.builder.ui.positioner_row_base import Positioner_RowWidgetBase
from pcdswidgets.builder.ui.positioner_row_tc_interlock_base import Positioner_Row_Tc_InterlockWidgetBase
from pcdswidgets.builder.ui.smaract_open_loop_base import Smaract_Open_LoopWidgetBase


class PositionerWidget(PositionerWidgetBase):
    _qt_designer_ = {
        "group": "PCDS Motion",
        "is_container": False,
    }


class PositionerRowWidget(Positioner_RowWidgetBase):
    _qt_designer_ = {
        "group": "PCDS Motion",
        "is_container": False,
    }


class PositionerRowTcInterlockWidget(Positioner_Row_Tc_InterlockWidgetBase):
    _qt_designer_ = {
        "group": "PCDS Motion",
        "is_container": False,
    }


class SmaractOpenLoopWidget(Smaract_Open_LoopWidgetBase):
    _qt_designer_ = {
        "group": "PCDS Motion",
        "is_container": False,
    }
