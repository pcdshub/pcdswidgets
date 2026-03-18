from pydm.widgets.qtplugins import ifont

from pcdswidgets.builder.ui.motor_record_full_base import MotorRecordFullBase


class MotorRecordFull(MotorRecordFullBase):
    _qt_designer_ = {
        "group": "PCDS Motion",
        "is_container": False,
        "icon": ifont.icon("expand-arrows-alt"),
    }
