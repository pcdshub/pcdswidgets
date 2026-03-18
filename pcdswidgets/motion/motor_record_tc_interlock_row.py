from pydm.widgets.qtplugins import ifont

from pcdswidgets.builder.ui.motor_record_tc_interlock_row_base import MotorRecordTcInterlockRowBase


class MotorRecordTcInterlockRow(MotorRecordTcInterlockRowBase):
    _qt_designer_ = {
        "group": "PCDS Motion",
        "is_container": False,
        "icon": ifont.icon("arrows-alt-h"),
    }
