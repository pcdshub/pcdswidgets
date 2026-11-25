"""
EtherCAT terminal states of one Beckhoff PLC (system summary screen).

Wraps one :class:`EthercatTerminalStatesStretch` (terminal tree with status roll-up,
filters and the selected terminal's state panel) and configures it from the macros.

Macros:
    PLC             PLC host name used for discovery, e.g. ``plc-sds-raptor`` (required)
    PREFIX          IOC PV prefix incl. trailing colon, e.g. ``PLC:ICL:IOC:`` (required)
    DISCOVERY       discovery JSON (default ``~/.cache/ecat-states/<PLC>.json``)
    CONFIRM         "0" -> state requests are sent without a confirmation dialog

Launch:
    pcdswidgets-show ethercat_terminal_states --PLC plc-sds-raptor --PREFIX PLC:ICL:IOC:
    pydm --stylesheet carbon_gray10.qss -m "PLC=plc-sds-raptor,PREFIX=PLC:ICL:IOC:" ethercat_terminal_states.py
"""

from pydm import Display
from qtpy import QtWidgets

from pcdswidgets.common.ethercat.constants import to_bool
from pcdswidgets.common.ethercat.ethercat_terminal_states_stretch import EthercatTerminalStatesStretch


class EthercatTerminalStates(Display):
    def __init__(self, parent=None, args=None, macros=None):
        super().__init__(parent=parent, args=args, macros=macros)
        macros = self.macros()  # Display stores the macros; returns {} if none

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.states = EthercatTerminalStatesStretch()
        self.states.setProperty("confirmRequests", to_bool(str(macros.get("CONFIRM", "1"))))
        self.states.setProperty("discoveryFile", str(macros.get("DISCOVERY", "")))
        self.states.setProperty("prefix", str(macros.get("PREFIX", "")))
        self.states.setProperty("plc", str(macros.get("PLC", "")))
        self.states.reload()  # apply all macros now instead of on the next event-loop turn
        self.setWindowTitle(self.states.DeviceName.text())
        layout.addWidget(self.states)
        self.resize(850, 1000)  # docked system-summary size

    def ui_filename(self):
        # UI is built in __init__, so there is no .ui file to load.
        return None

    def closeEvent(self, event):
        self.states.teardown()
        super().closeEvent(event)
