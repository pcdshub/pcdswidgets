"""Mixin classes that add EPICS channel behavior to vacuum symbol widgets."""

import logging
import os
from functools import partial

from pydm.widgets.channel import PyDMChannel
from pydm.widgets.enum_button import PyDMEnumButton
from pydm.widgets.label import PyDMLabel
from pydm.widgets.pushbutton import PyDMPushButton
from qtpy.QtCore import Property, Qt
from qtpy.QtWidgets import QGridLayout, QVBoxLayout

logger = logging.getLogger(__name__)


class InterlockMixin:
    """
    Add an interlock channel and ``interlocked`` property to the widget.

    The interlocked property can be used at stylesheet in the following manner:


    .. code-block:: css

        *[interlocked="true"] {
            background-color: red;
        }

    Parameters
    ----------
    interlock_suffix : str
        The suffix to be used along with the channelPrefix from PCDSSymbolBase
        to compose the interlock channel address.
    """

    def __init__(self, interlock_suffix, **kwargs):
        """Store the interlock suffix and initialize the interlock state."""
        self._interlock_suffix = interlock_suffix
        self._interlocked = False
        self._interlock_connected = False
        self.interlock_channel = None
        super().__init__(**kwargs)

    @Property(bool, designable=False)
    def interlocked(self):
        """
        Query the interlock state.

        Returns
        -------
        bool
        """
        return self._interlocked

    def create_channels(self):
        """
        Add the interlock channel on top of the super class channels.

        Also resets the interlocked and interlock_connected variables.
        """
        super().create_channels()
        if not self._interlock_suffix:
            return

        self._interlocked = True
        self._interlock_connected = False

        self.interlock_channel = PyDMChannel(
            address="{}{}".format(self._channels_prefix, self._interlock_suffix),
            connection_slot=self.interlock_connection_changed,
            value_slot=self.interlock_value_changed,
        )
        self.interlock_channel.connect()

    def status_tooltip(self):
        """
        Add the interlock mixin's contribution to the status tooltip.

        Returns
        -------
        str
        """
        status = super().status_tooltip()
        if status:
            status += os.linesep
        status += f"Interlocked: {self.interlocked}"
        return status

    def interlock_connection_changed(self, conn):
        """
        Handle a connection status change on the Interlock Channel.

        Parameters
        ----------
        conn : bool
            True if connected, False otherwise.
        """
        self._interlock_connected = conn

    def interlock_value_changed(self, value):
        """
        Handle a value change on the Interlock Channel.

        Parameters
        ----------
        value : int
            The value from the channel will be either 0 or 1 with 0 meaning
            that the widget is interlocked.
        """
        self._interlocked = value == 0
        self.controls_frame.setEnabled(not self._interlocked)
        self.update_stylesheet()
        self.update_status_tooltip()


class ErrorMixin:
    """
    Add an error channel and ``error`` property to the widget.

    The error property can be used at stylesheet in the following manner:

    .. code-block:: css

        *[error="INVALID"] {
            color: purple;
        }

    Parameters
    ----------
    error_suffix : str
        The suffix to be used along with the channelPrefix from PCDSSymbolBase
        to compose the error channel address.
    """

    def __init__(self, error_suffix, **kwargs):
        """Store the error suffix and initialize the error state."""
        self._error_suffix = error_suffix
        self._error = ""
        self._error_value = None
        self._error_enum = []
        self._error_connected = False
        self.error_channel = None
        super().__init__(**kwargs)

    @Property(str, designable=False)
    def error(self):
        """
        Query the error state.

        Returns
        -------
        str
        """
        return self._error

    def create_channels(self):
        """
        Add the error channel on top of the super class channels.

        Also resets the error and error_connected variables.
        """
        super().create_channels()
        if not self._error_suffix:
            return

        self._error_connected = False
        self._error = ""

        self.error_channel = PyDMChannel(
            address=f"{self._channels_prefix}{self._error_suffix}",
            connection_slot=self.error_connection_changed,
            value_slot=self.error_value_changed,
            enum_strings_slot=self.error_enum_changed,
        )
        self.error_channel.connect()

    def status_tooltip(self):
        """
        Add the error mixin's contribution to the status tooltip.

        Returns
        -------
        str
        """
        status = super().status_tooltip()
        status += os.linesep
        status += f"Error: {self.error}"
        return status

    def error_connection_changed(self, conn):
        """
        Handle a connection status change on the Error Channel.

        Parameters
        ----------
        conn : bool
            True if connected, False otherwise.
        """
        self._error_connected = conn

    def error_enum_changed(self, items):
        """
        Handle an enum-strings change on the Error Channel.

        This callback triggers the update of the error message and also a
        repaint of the widget with the new stylesheet guidelines for the
        current error value.

        Parameters
        ----------
        items : tuple
            The string items
        """
        if items is None:
            return
        self._error_enum = items
        self._update_error_msg()

    def error_value_changed(self, value):
        """
        Handle a value change on the Error Channel.

        This callback triggers the update of the error message and also a
        repaint of the widget with the new stylesheet guidelines for the
        current error value.

        Parameters
        ----------
        value : int
        """
        if value is None:
            return
        self._error_value = value
        self._update_error_msg()

    def _update_error_msg(self):
        """Update the error property and refresh the stylesheet and tooltip."""
        if self._error_value is None:
            return
        if len(self._error_enum) > 0:
            try:
                self._error = self._error_enum[self._error_value]
            except IndexError:
                self._error = ""
        else:
            self._error = str(self._error_value)
        self.update_stylesheet()
        self.update_status_tooltip()


class StateMixin:
    """
    Add a state channel and ``state`` property to the widget.

    The state property can be used at stylesheet in the following manner:

    .. code-block:: css

        *[state="Vented"] {
            border: 5px solid blue;
        }

    Parameters
    ----------
    state_suffix : str
        The suffix to be used along with the channelPrefix from PCDSSymbolBase
        to compose the state channel address.
    """

    def __init__(self, state_suffix, **kwargs):
        """Store the state suffix and initialize the state."""
        self._state_suffix = state_suffix
        self._state = ""
        self._state_value = None
        self._state_enum = []
        self._state_connected = False
        self.state_channel = None
        super().__init__(**kwargs)

    @Property(str, designable=False)
    def state(self):
        """
        Query the state of the widget.

        Returns
        -------
        str
        """
        return self._state

    def create_channels(self):
        """
        Add the state channel on top of the super class channels.

        Also resets the state and state_connected variables.
        """
        super().create_channels()
        if not self._state_suffix:
            return

        self._state_connected = False
        self._state = ""

        self.state_channel = PyDMChannel(
            address=f"{self._channels_prefix}{self._state_suffix}",
            connection_slot=self.state_connection_changed,
            value_slot=self.state_value_changed,
            enum_strings_slot=self.state_enum_changed,
        )
        self.state_channel.connect()

    def status_tooltip(self):
        """
        Add the state mixin's contribution to the status tooltip.

        Returns
        -------
        str
        """
        status = super().status_tooltip()
        if status:
            status += os.linesep
        status += f"State: {self.state}"
        return status

    def state_connection_changed(self, conn):
        """
        Handle a connection status change on the State Channel.

        Parameters
        ----------
        conn : bool
            True if connected, False otherwise.
        """
        self._state_connected = conn

    def state_enum_changed(self, items):
        """
        Handle an enum-strings change on the State Channel.

        This callback triggers the update of the state message and also a
        repaint of the widget with the new stylesheet guidelines for the
        current state value.

        Parameters
        ----------
        items : tuple
            The string items
        """
        if items is None:
            return
        self._state_enum = items
        self._update_state_msg()

    def state_value_changed(self, value):
        """
        Handle a value change on the State Channel.

        This callback triggers the update of the state message and also a
        repaint of the widget with the new stylesheet guidelines for the
        current state value.

        Parameters
        ----------
        value : int
        """
        if value is None:
            return
        self._state_value = value
        self._update_state_msg()

    def _update_state_msg(self):
        """Update the state property and refresh the stylesheet and tooltip."""
        if self._state_value is None:
            return
        if len(self._state_enum) > 0:
            try:
                self._state = self._state_enum[self._state_value]
            except IndexError:
                self._state = ""
        else:
            self._state = str(self._state_value)
        self.update_stylesheet()
        self.update_status_tooltip()


class OpenCloseStateMixin:
    """
    Add open/close channels and a combined ``state`` property to the widget.

    The state property can be used at stylesheet in the following manner:

    .. code-block:: css

        *[state="Close"] {
            background-color: blue;
        }

    Parameters
    ----------
    open_suffix : str
        The suffix to be used along with the channelPrefix from PCDSSymbolBase
        to compose the open state channel address.
    close_suffix : str
        The suffix to be used along with the channelPrefix from PCDSSymbolBase
        to compose the close state channel address.
    """

    def __init__(self, open_suffix, close_suffix, **kwargs):
        """Store the open/close suffixes and initialize channel state."""
        self._open_suffix = open_suffix
        self._close_suffix = close_suffix

        self._state_open = False
        self._state_close = False

        self._open_connected = False
        self._close_connected = False

        self.state_open_channel = None
        self.state_close_channel = None
        super().__init__(**kwargs)

    @Property(str, designable=False)
    def state(self):
        """
        Query the combined open/close state of the widget.

        Returns
        -------
        str
            The return string will either be `Open`, `Close` or `INVALID` when
            it was not possible to determine the state.
        """
        if self._state_open == self._state_close:
            return "INVALID"
        if self._state_open:
            return "Open"
        else:
            return "Close"

    def create_channels(self):
        """
        Add the open and close state channels on top of the super class channels.

        Also resets the state and interlock_connected variables.
        """
        super().create_channels()
        if not self._open_suffix or not self._close_suffix:
            return

        self._open_connected = False
        self._close_connected = False
        self._state_open = False
        self._state_close = False
        self._state = "INVALID"

        self.state_open_channel = PyDMChannel(
            address=f"{self._channels_prefix}{self._open_suffix}",
            connection_slot=partial(self.state_connection_changed, "OPEN"),
            value_slot=partial(self.state_value_changed, "OPEN"),
        )
        self.state_open_channel.connect()

        self.state_close_channel = PyDMChannel(
            address=f"{self._channels_prefix}{self._close_suffix}",
            connection_slot=partial(self.state_connection_changed, "CLOSE"),
            value_slot=partial(self.state_value_changed, "CLOSE"),
        )
        self.state_close_channel.connect()

    def status_tooltip(self):
        """
        Add the open/close state mixin's contribution to the status tooltip.

        Returns
        -------
        str
        """
        status = super().status_tooltip()
        if status:
            status += os.linesep
        status += f"State: {self.state}"
        return status

    def state_connection_changed(self, which, conn):
        """
        Handle a connection status change on the open or close channel.

        Parameters
        ----------
        which : str
            String defining which channel is sending the information. It must
            be either "OPEN" or "CLOSE".
        conn : bool
            True if connected, False otherwise.
        """
        if which == "OPEN":
            self._open_connected = conn
        else:
            self._close_connected = conn

    def state_value_changed(self, which, value):
        """
        Handle a value change on the open or close channel.

        Parameters
        ----------
        which : str
            String defining which channel is sending the information. It must
            be either "OPEN" or "CLOSE".
        value : int
            The value from the channel which will be either 0 or 1 with 1
            meaning that a certain state is active.
        """
        if which == "OPEN":
            self._state_open = value
        else:
            self._state_close = value

        self.update_stylesheet()
        self.update_status_tooltip()


class ButtonControl:
    """
    Add a PyDMEnumButton to the widget for controls.

    Parameters
    ----------
    command_suffix : str
        The suffix to be used along with the channelPrefix from PCDSSymbolBase
        to compose the command button channel address.
    """

    def __init__(self, command_suffix, **kwargs):
        """Store the command suffix and build the control button layout."""
        self._command_suffix = command_suffix
        self._orientation = Qt.Horizontal
        self.control_btn = PyDMEnumButton()
        self.control_btn.checkable = False
        self.controlButtonHorizontal = True
        self.controls_layout = QVBoxLayout()
        self.controls_layout.setSpacing(2)
        self.controls_layout.setContentsMargins(0, 10, 0, 0)
        super().__init__(**kwargs)
        self.controls_frame.setLayout(self.controls_layout)
        self.controls_frame.layout().addWidget(self.control_btn)

    @Property(bool)
    def controlButtonHorizontal(self):
        """Return whether the control button is laid out horizontally."""
        return self._orientation == Qt.Horizontal

    @controlButtonHorizontal.setter
    def controlButtonHorizontal(self, checked):
        """Set the control button orientation to horizontal when ``checked``."""
        if checked:
            self._orientation = Qt.Horizontal
            self.control_btn.setMinimumSize(100, 40)
        else:
            self._orientation = Qt.Vertical
            self.control_btn.setMinimumSize(40, 80)

        self.control_btn.orientation = self._orientation

    def create_channels(self):
        """
        Create the widget's channels and wire up the control button.

        This method also sets the channel address for the control button.
        """
        super().create_channels()
        if self._channels_prefix:
            self.control_btn.channel = "{}{}".format(self._channels_prefix, self._command_suffix)

    def destroy_channels(self):
        """
        Destroy the widget's channels and clear the control button.

        This method also clears the channel address for the control button.
        """
        super().destroy_channels()
        self.control_btn.channel = None


class LabelControl:
    """
    Add a PyDMLabel to the widget for controls.

    Parameters
    ----------
    readback_suffix : str
        The suffix to be used along with the channelPrefix from PCDSSymbolBase
        to compose the readback label channel address.
    readback_name : str
        The name to be set to the PyDMLabel so one can refer to it by name
        with stylesheet
    """

    def __init__(self, readback_suffix, readback_name, **kwargs):
        """Store the readback suffix and build the readback label layout."""
        self._readback_suffix = readback_suffix
        self.readback_label = PyDMLabel()
        if readback_name:
            self.readback_label.setObjectName(readback_name)
        self.readback_label.setAlignment(Qt.AlignCenter)
        self.controls_layout = QVBoxLayout()
        self.controls_layout.setSpacing(2)
        self.controls_layout.setContentsMargins(0, 10, 0, 0)
        super().__init__(**kwargs)
        self.controls_frame.setLayout(self.controls_layout)
        self.controls_frame.layout().addWidget(self.readback_label)

    def create_channels(self):
        """
        Create the widget's channels and wire up the readback label.

        This method also sets the channel address for the control button.
        """
        super().create_channels()
        if self._channels_prefix:
            self.readback_label.channel = "{}{}".format(self._channels_prefix, self._readback_suffix)

    def destroy_channels(self):
        """
        Destroy the widget's channels and clear the readback label.

        This method also clears the channel address for the control button.
        """
        super().destroy_channels()
        self.readback_label.channel = None


class ButtonLabelControl(ButtonControl):
    """
    Add a PyDMEnumButton and a PyDMLabel to the widget for controls.

    Parameters
    ----------
    command_suffix : str
        The suffix to be used along with the channelPrefix from PCDSSymbolBase
        to compose the command button channel address.
    readback_suffix : str
        The suffix to be used along with the channelPrefix from PCDSSymbolBase
        to compose the readback label channel address.
    readback_name : str
        The name to be set to the PyDMLabel so one can refer to it by name
        with stylesheet
    """

    def __init__(self, command_suffix, readback_suffix, readback_name, **kwargs):
        """Store the command and readback suffixes and build the controls."""
        self._readback_suffix = readback_suffix

        self.readback_label = PyDMLabel()
        self.readback_label.setObjectName(readback_name)
        self.readback_label.setAlignment(Qt.AlignCenter)
        super().__init__(command_suffix, **kwargs)
        self.controls_frame.layout().insertWidget(0, self.readback_label)

    def create_channels(self):
        """
        Create the widget's channels and wire up the readback label.

        This method also sets the channel address for the control button.
        """
        super().create_channels()
        if self._channels_prefix:
            self.readback_label.channel = "{}{}".format(self._channels_prefix, self._readback_suffix)

    def destroy_channels(self):
        """
        Destroy the widget's channels and clear the readback label.

        This method also clears the channel address for the control button.
        """
        super().destroy_channels()
        self.readback_label.channel = None


class MultipleButtonControl:
    """
    Add multiple PyDMPushButton instances to the widget for controls.

    Parameters
    ----------
    commands : list
        List of dictionaries containing the specifications for the buttons.
        Required keys for now are:

        - suffix: str
            suffix to be used along with the channelPrefix from PCDSSymbolBase
            to compose the command button channel address
        - text: str
            the text to display at the button
        - value
            the value to be written when the button is pressed
    """

    def __init__(self, *, commands, **kwargs):
        """Store the button configs and build the button grid layout."""
        self._command_buttons_config = commands
        self._orientation = Qt.Horizontal
        self.buttons = []
        self.create_buttons()

        super().__init__(**kwargs)
        self.controls_frame.setLayout(QGridLayout())
        self.controlButtonHorizontal = True

    @Property(bool)
    def controlButtonHorizontal(self):
        """Return whether the control buttons are laid out horizontally."""
        return self._orientation == Qt.Horizontal

    @controlButtonHorizontal.setter
    def controlButtonHorizontal(self, checked):
        """Rebuild the layout with horizontal orientation when ``checked``."""
        self.clear_control_layout()

        self._orientation = Qt.Vertical
        if checked:
            self._orientation = Qt.Horizontal

        layout = self.controls_frame.layout()

        if self._orientation == Qt.Vertical:
            for i, btn in enumerate(self.buttons):
                layout.addWidget(btn, i, 0)
        elif self._orientation == Qt.Horizontal:
            for i, btn in enumerate(self.buttons):
                layout.addWidget(btn, 0, i)

    def clear_control_layout(self):
        """Remove all inner widgets from the control layout."""
        layout = self.controls_frame.layout()
        if not isinstance(layout, QGridLayout):
            return
        for col in range(0, layout.columnCount()):
            for row in range(0, layout.rowCount()):
                item = layout.itemAtPosition(row, col)
                if item is not None:
                    w = item.widget()
                    if w is not None:
                        layout.removeWidget(w)

    def create_buttons(self):
        """Create PyDMPushButton widgets from the stored button configs."""
        for btn in self._command_buttons_config:
            try:
                text = btn["text"]
                value = btn["value"]
                btn = PyDMPushButton(label=text, pressValue=value)
                self.buttons.append(btn)
            except KeyError:
                logger.exception("Invalid config for MultipleButtonControl.")

    def create_channels(self):
        """
        Create the widget's channels and wire up each command button.

        This method also sets the channel address for the control button.
        """
        super().create_channels()
        if self._channels_prefix:
            for idx, btn in enumerate(self.buttons):
                suffix = self._command_buttons_config[idx]["suffix"]
                btn.channel = f"{self._channels_prefix}{suffix}"

    def destroy_channels(self):
        """
        Destroy the widget's channels and clear each command button.

        This method also clears the channel address for the control button.
        """
        super().destroy_channels()
        for btn in self.buttons:
            btn.channel = None
