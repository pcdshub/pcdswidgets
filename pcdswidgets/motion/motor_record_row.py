from pydm.widgets.qtplugins import ifont

from pcdswidgets.builder.ui.motor_record_row_base import MotorRecordRowBase


class MotorRecordRow(MotorRecordRowBase):
    _qt_designer_ = {
        "group": "PCDS Motion",
        "is_container": False,
        "icon": ifont.icon("arrows-alt-h"),
    }
