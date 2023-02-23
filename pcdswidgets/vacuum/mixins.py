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
    The InterlockMixin class adds the interlock channel and `interlocked`
    property to the widget.

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
        self._interlock_suffix = interlock_suffix
        self._interlocked = False
        self._interlock_connected = False
        self.interlock_channel = None
        super().__init__(**kwargs)

    @Property(bool, designable=False)
    def interlocked(self):
        """
        Property used to query interlock state.

        Returns
        -------
        bool
        """
        return self._interlocked

    def create_channels(self):
        """
        This method invokes `create_channels` from the super classes and adds
        the `interlock_channel` to the widget along with a reset for the
        interlocked and interlock_connected variables.
        """
        super().create_channels()
        if not self._interlock_suffix:
            return

        self._interlocked = True
        self._interlock_connected = False

        self.interlock_channel = PyDMChannel(
            address="{}{}".format(self._channels_prefix,
                                  self._interlock_suffix),
            connection_slot=self.interlock_connection_changed,
            value_slot=self.interlock_value_changed
        )
        self.interlock_channel.connect()

    def status_tooltip(self):
        """
        This method adds the contribution of the interlock mixin into the
        general status tooltip.

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
        Callback invoked when the connection status changes for the Interlock
        Channel.

        Parameters
        ----------
        conn : bool
            True if connected, False otherwise.
        """
        self._interlock_connected = conn

    def interlock_value_changed(self, value):
        """
        Callback invoked when the value changes for the Interlock Channel.

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
    The ErrorMixin class adds the error channel and `error`
    property to the widget.

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
        Property used to query the error state.

        Returns
        -------
        str
        """
        return self._error

    def create_channels(self):
        """
        This method invokes `create_channels` from the super classes and adds
        the `error_channel` to the widget along with a reset for the error and
        error_connected variables.
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
            enum_strings_slot=self.error_enum_changed
        )
        self.error_channel.connect()

    def status_tooltip(self):
        """
        This method adds the contribution of the error mixin into the general
        status tooltip.

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
        Callback invoked when the connection status changes for the Error
        Channel.

        Parameters
        ----------
        conn : bool
            True if connected, False otherwise.
        """
        self._error_connected = conn

    def error_enum_changed(self, items):
        """
        Callback invoked when the enumeration strings change for the Error
        Channel.
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
        Callback invoked when the value change for the Error Channel.
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
        """
        Internal method that updates the error property and triggers an update
        on the stylesheet and tooltip.
        """
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
    The StateMixin class adds the state channel and `state` property to the
    widget.

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
        Property used to query the state of the widget.

        Returns
        -------
        str
        """
        return self._state

    def create_channels(self):
        """
        This method invokes `create_channels` from the super classes and adds
        the `state_channel` to the widget along with a reset for the
        state and state_connected variables.
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
            enum_strings_slot=self.state_enum_changed
        )
        self.state_channel.connect()

    def status_tooltip(self):
        """
        This method adds the contribution of the state mixin into the general
        status tooltip.

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
        Callback invoked when the connection status changes for the State
        Channel.

        Parameters
        ----------
        conn : bool
            True if connected, False otherwise.
        """
        self._state_connected = conn

    def state_enum_changed(self, items):
        """
        Callback invoked when the enumeration strings change for the State
        Channel.
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
        Callback invoked when the value change for the State Channel.
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
        """
        Internal method that updates the state property and triggers an update
        on the stylesheet and tooltip.
        """
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
    The OpenCloseStateMixin class adds two channels (Open and Close State) and
    a `state` property based on a combination of the two channels to the
    widget.

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
        Property used to query the state of the widget.

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
        This method invokes `create_channels` from the super classes and adds
        the `state_open_channel` and `state_close_channel` to the widget along
        with a reset for the state and interlock_connected variables.
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
            value_slot=partial(self.state_value_changed, "OPEN")
        )
        self.state_open_channel.connect()

        self.state_close_channel = PyDMChannel(
            address=f"{self._channels_prefix}{self._close_suffix}",
            connection_slot=partial(self.state_connection_changed, "CLOSE"),
            value_slot=partial(self.state_value_changed, "CLOSE")
        )
        self.state_close_channel.connect()

    def status_tooltip(self):
        """
        This method adds the contribution of the open close state mixin into
        the general status tooltip.

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
        Callback invoked when the connection status changes for one of the
        channels in this mixin.

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
        Callback invoked when the value changes for one of the channels in this
        mixin.

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
    The ButtonControl class adds a PyDMEnumButton to the widget for controls.

    Parameters
    ----------
    command_suffix : str
        The suffix to be used along with the channelPrefix from PCDSSymbolBase
        to compose the command button channel address.
    """
    def __init__(self, command_suffix, **kwargs):
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
        return self._orientation == Qt.Horizontal

    @controlButtonHorizontal.setter
    def controlButtonHorizontal(self, checked):
        if checked:
            self._orientation = Qt.Horizontal
            self.control_btn.setMinimumSize(100, 40)
        else:
            self._orientation = Qt.Vertical
            self.control_btn.setMinimumSize(40, 80)

        self.control_btn.orientation = self._orientation

    def create_channels(self):
        """
        Method invoked when the channels associated with the widget must be
        created.
        This method also sets the channel address for the control button.
        """
        super().create_channels()
        if self._channels_prefix:
            self.control_btn.channel = "{}{}".format(self._channels_prefix,
                                                     self._command_suffix)

    def destroy_channels(self):
        """
        Method invoked when the channels associated with the widget must be
        destroyed.
        This method also clears the channel address for the control button.
        """
        super().destroy_channels()
        self.control_btn.channel = None


class LabelControl:
    """
    The LabelControl class adds a PyDMLabel to the widget for controls.

    Parameters
    ----------
    readback_suffix : str
        The suffix to be used along with the channelPrefix from PCDSSymbolBase
        to compose the readback label channel address.
    readback_name : str
        The name to be set to the PyDMLabel so one can refer to it by name
        with stylesheet
    """
    def __init__(self, readback_suffix, readback_name,
                 **kwargs):
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
        Method invoked when the channels associated with the widget must be
        created.
        This method also sets the channel address for the control button.
        """
        super().create_channels()
        if self._channels_prefix:
            self.readback_label.channel = "{}{}".format(self._channels_prefix,
                                                        self._readback_suffix)

    def destroy_channels(self):
        """
        Method invoked when the channels associated with the widget must be
        destroyed.
        This method also clears the channel address for the control button.
        """
        super().destroy_channels()
        self.readback_label.channel = None


class ButtonLabelControl(ButtonControl):
    """
    The ButtonLabelControl class adds a PyDMEnumButton and a PyDMLabel to the
    widget for controls.

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
    def __init__(self, command_suffix, readback_suffix, readback_name,
                 **kwargs):
        self._readback_suffix = readback_suffix

        self.readback_label = PyDMLabel()
        self.readback_label.setObjectName(readback_name)
        self.readback_label.setAlignment(Qt.AlignCenter)
        super().__init__(command_suffix, **kwargs)
        self.controls_frame.layout().insertWidget(0, self.readback_label)

    def create_channels(self):
        """
        Method invoked when the channels associated with the widget must be
        created.
        This method also sets the channel address for the control button.
        """
        super().create_channels()
        if self._channels_prefix:
            self.readback_label.channel = "{}{}".format(self._channels_prefix,
                                                        self._readback_suffix)

    def destroy_channels(self):
        """
        Method invoked when the channels associated with the widget must be
        destroyed.
        This method also clears the channel address for the control button.
        """
        super().destroy_channels()
        self.readback_label.channel = None


class MultipleButtonControl:
    """
    The MultipleButtonControl class adds multiple PyDMPushButton instances to
    the widget for controls.

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
        self._command_buttons_config = commands
        self._orientation = Qt.Horizontal
        self.buttons = []
        self.create_buttons()

        super().__init__(**kwargs)
        self.controls_frame.setLayout(QGridLayout())
        self.controlButtonHorizontal = True

    @Property(bool)
    def controlButtonHorizontal(self):
        return self._orientation == Qt.Horizontal

    @controlButtonHorizontal.setter
    def controlButtonHorizontal(self, checked):
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
        """
        Remove all inner widgets from the control layout
        """
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
        for btn in self._command_buttons_config:
            try:
                text = btn['text']
                value = btn['value']
                btn = PyDMPushButton(label=text, pressValue=value)
                self.buttons.append(btn)
            except KeyError:
                logger.exception('Invalid config for MultipleButtonControl.')

    def create_channels(self):
        """
        Method invoked when the channels associated with the widget must be
        created.
        This method also sets the channel address for the control button.
        """
        super().create_channels()
        if self._channels_prefix:
            for idx, btn in enumerate(self.buttons):
                suffix = self._command_buttons_config[idx]['suffix']
                btn.channel = f"{self._channels_prefix}{suffix}"

    def destroy_channels(self):
        """
        Method invoked when the channels associated with the widget must be
        destroyed.
        This method also clears the channel address for the control button.
        """
        super().destroy_channels()
        for btn in self.buttons:
            btn.channel = None
