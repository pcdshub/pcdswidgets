"""Module for ExpertScreenLauncher"""

# Originally generated from jinja template ui_main_widget.j2
# This file can be safely edited to change the runtime behavior of the widget.
import logging
import threading

from epics import get_pv
from pydm.widgets import PyDMShellCommand
from qtpy.QtCore import Signal

from pcdswidgets.builder.designer_options import DesignerOptions
from pcdswidgets.builder.designer_widget import DesignerWidget
from pcdswidgets.builder.icon_options import IconOptions

try:
    from qtpy.QtCore import pyqtProperty
except ImportError:
    from qtpy.QtCore import Property as pyqtProperty  # type: ignore

logger = logging.getLogger(__name__)


class ExpertScreenLauncher(PyDMShellCommand, DesignerWidget):
    _macro_to_widget = {}
    _widget_to_macro = {}
    _widget_to_pre_template = {}

    # Signals for shenanigans
    _script_received = Signal(str)

    designer_options = DesignerOptions(
        is_container=False,
        group="ECS Common Tools",
        icon=IconOptions.NONE,
    )

    editable_str_properties = {"prefix": "", "expert_screen_script": ""}

    def __init__(self, *args, **kwargs):
        self._macro_values = {}
        self._prefix = None
        self._expert_screen_script = None
        super().__init__(*args, **kwargs)
        self._script_received.connect(self.update_script)
        self.setEnabled(False)

    # ---------------------pyqtProperties----------------------------------------------- #
    def get_prefix(self):
        return self._prefix

    def set_prefix(self, value: str | None = None):
        self._prefix = value
        self.find_launch_gui_pv()

    prefix = pyqtProperty(str, get_prefix, set_prefix)

    def get_expert_screen_script(self):
        return self._expert_screen_script

    def set_expert_screen_script(self, value: str | None = None):
        if value:
            self._expert_screen_script = value
            self.setCommands([value])

    expert_screen_script = pyqtProperty(str, get_expert_screen_script, set_expert_screen_script)

    # ---------------------Expert Screen PV methods------------------------------------- #
    def find_launch_gui_pv(self):
        """
        Try to connect to a LAUNCH_GUI record for the supplied PV.
        There are 3 standard ways these records are written:
            * :LAUNCH_GUI -- e.g. iocAdmin
            * :LAUNCH_EDM -- e.g. iocAdmin
            * :LAUNCH_GUI.VAL$ -- e.g. lsi record

        Try to get_pv all 3 and whoever connects and wins gets to set the script.
        Abandon the rest.
        """
        typical_pvs = ["LAUNCH_GUI", "LAUNCH_EDM", "LAUNCH_GUI.VAL$"]

        if self.get_prefix():
            for suffix in typical_pvs:
                # Note, if the record is actually an LSI, the first PV will connect
                # but truncate at 41 char, so the final case will fill it out
                logger.debug(f"Attempting to connect to {self.get_prefix()}:{suffix}")
                get_pv(f"{self.get_prefix()}:{suffix}", connection_callback=self._on_launch_gui_connection_change)

    def _on_launch_gui_connection_change(self, pvname: str | None = None, conn: bool | None = None, **kws):
        """
        Update the expert_screen_script attr when the pv actually connects.
        Since iocAdmin launch EDM/GUI PVs are waveforms and not ``lsi``,
        the .VAL$ will not connect. Else, for ``lsi`` records both LAUNCH_GUI
        and LAUNCH_GUI.VAL$ are valid and connect. The latter overwrites.
        """

        if conn:
            logger.debug(f"{pvname} connection successful")
            # Spawn this on a thread to avoid strange behavior and blocking calls
            # Normally you'd handle this with ca:// but we are doing trickery here
            threading.Thread(target=self._read_pv, args=(pvname,), daemon=True).start()

    def _read_pv(self, pvname: str | None = None):
        """
        Read the LAUNCH_GUI/EDM PV as a string, if it exists.
        """
        value = get_pv(pvname).get(as_string=True)
        logger.debug(f"{pvname} returns {value}")
        if value:
            self._script_received.emit(value)

    def update_script(self, new_value: str | None = None):
        """
        Once a thread from _read_pv gets the initial value from the PV,
        validate the new string and apply it when ready.
        """

        # can still get None on first call if CA isn't given time
        if not new_value:
            logger.debug("_script_received emitted with no value")
            return

        current_value = self.get_expert_screen_script()

        if current_value and new_value:
            # Not guaranteed LAUNCH_GUI executes before LAUNCH_GUI.VAL$
            if len(new_value) < len(current_value) and new_value in current_value:
                # Then we got the 41 char substring, but had the real one already
                return
            elif current_value != new_value:
                # Got a new update, yipee!
                logger.debug(f"Updating expert screen script to: {new_value}")
            else:
                # Nothing new or we set this in designer explicitly.
                self.setEnabled(True)
        else:
            # It's okay if this wasn't set before
            logger.debug(f"Setting expert screen script to: {new_value}")

        self.set_expert_screen_script(new_value)
        self.setEnabled(True)
