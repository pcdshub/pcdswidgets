from pydm.widgets.enum_button import PyDMEnumButton
from pydm.widgets.label import PyDMLabel
from qtpy.QtCore import QSize, Property, Q_ENUMS, Qt
from qtpy.QtWidgets import QVBoxLayout, QSizePolicy

from .base import PCDSSymbolBase, ContentLocation
from .mixins import StateMixin, InterlockMixin
from ..icons.gauges import (PiraniGaugeSymbolIcon, HotCathodeGaugeSymbolIcon,
                            ColdCathodeGaugeSymbolIcon)


class PiraniGauge(StateMixin, PCDSSymbolBase, ContentLocation):
    """
    A Symbol Widget representing a Pirani Gauge with the proper icon and
    controls.

    Parameters
    ----------
    parent : QWidget
        The parent widget for the symbol

    Notes
    -----
    This widget allow for high customization through the Qt Stylesheets
    mechanism.
    As this widget is composed by internal widgets, their names can be used as
    selectors when writing your stylesheet to be used with this widget.
    Properties are also available to offer wider customization possibilities.

    **Internal Components**

    +-----------+--------------+---------------------------------------+
    |Widget Name|Type          |What is it?                            |
    +===========+==============+=======================================+
    |controls   |QFrame        |The QFrame wrapping the controls panel.|
    +-----------+--------------+---------------------------------------+
    |icon       |BaseSymbolIcon|The widget containing the icon drawing.|
    +-----------+--------------+---------------------------------------+
    |pressure   |PyDMLabel     |The pressure reading label.            |
    +-----------+--------------+---------------------------------------+

    **Additional Properties**

    +-----------+-------------------------------------------------------------+
    |Property   |Values                                                       |
    +===========+=============================================================+
    |state      |`On` or `Off`                                                |
    +-----------+-------------------------------------------------------------+

    Examples
    --------

    .. code-block:: css

        PiraniGauge [state="Off"] {
            qproperty-brush: red;
            color: gray;
        }
        PiraniGauge [state="On"] {
            qproperty-brush: green;
            color: black;
        }

    """
    _state_suffix = ":PRESS_OK"
    _readback_suffix = ":PRESS"

    Q_ENUMS(ContentLocation)
    NAME = "Pirani Gauge"

    def __init__(self, parent=None, **kwargs):
        super(PiraniGauge, self).__init__(parent=parent,
                                          state_suffix=self._state_suffix,
                                          **kwargs)

        self.pressure_label = PyDMLabel(self)
        self.pressure_label.setObjectName("pressure")
        self.icon = PiraniGaugeSymbolIcon(self)
        self.icon.setMinimumSize(16, 16)
        self.icon.setSizePolicy(QSizePolicy.Expanding,
                                QSizePolicy.Expanding)
        self.icon.setVisible(self._show_icon)
        self.iconSize = 32

        self.controls_layout = QVBoxLayout()
        self.controls_layout.setSpacing(0)
        self.controls_layout.setContentsMargins(0, 0, 0, 0)
        self.controls_frame.setLayout(self.controls_layout)
        self.controls_frame.layout().addWidget(self.pressure_label)

        self.assemble_layout()
        self.update_status_tooltip()

    @Property(ContentLocation)
    def controlsLocation(self):
        """
        Property controlling where the controls frame will be displayed.

        Returns
        -------
        location : ContentLocation
        """
        return self._controls_location

    @controlsLocation.setter
    def controlsLocation(self, location):
        """
        Property controlling where the controls frame will be displayed.

        Parameters
        ----------
        location : ContentLocation
        """
        if location != self._controls_location:
            self._controls_location = location
            self.assemble_layout()

    def sizeHint(self):
        """
        Suggested initial size for the widget.

        Returns
        -------
        size : QSize
        """
        return QSize(200, 200)

    def create_channels(self):
        """
        Method invoked when the channels associated with the widget must be
        created.
        This method also sets the channel address for the control button.
        """
        super(PiraniGauge, self).create_channels()
        if self._channels_prefix:
            self.pressure_label.channel = "{}{}".format(self._channels_prefix,
                                                        self._readback_suffix)

    def destroy_channels(self):
        """
        Method invoked when the channels associated with the widget must be
        destroyed.
        This method also clears the channel address for the control button.
        """
        super(PiraniGauge, self).destroy_channels()
        self.pressure_label.channel = None


class HotCathodeGauge(InterlockMixin, StateMixin, PCDSSymbolBase,
                      ContentLocation):
    """
    A Symbol Widget representing an Ion Pump with the proper icon and controls.

    Parameters
    ----------
    parent : QWidget
        The parent widget for the symbol

    Notes
    -----
    This widget allow for high customization through the Qt Stylesheets
    mechanism.
    As this widget is composed by internal widgets, their names can be used as
    selectors when writing your stylesheet to be used with this widget.
    Properties are also available to offer wider customization possibilities.

    **Internal Components**

    +-----------+--------------+---------------------------------------+
    |Widget Name|Type          |What is it?                            |
    +===========+==============+=======================================+
    |interlock  |QFrame        |The QFrame wrapping this whole widget. |
    +-----------+--------------+---------------------------------------+
    |controls   |QFrame        |The QFrame wrapping the controls panel.|
    +-----------+--------------+---------------------------------------+
    |icon       |BaseSymbolIcon|The widget containing the icon drawing.|
    +-----------+--------------+---------------------------------------+
    |pressure   |PyDMLabel     |The pressure reading label.            |
    +-----------+--------------+---------------------------------------+

    **Additional Properties**

    +-----------+-------------------------------------------------------------+
    |Property   |Values                                                       |
    +===========+=============================================================+
    |interlocked|`true` or `false`                                            |
    +-----------+-------------------------------------------------------------+
    |state      |`On`, `Off`, `Starting` or `Error`                           |
    +-----------+-------------------------------------------------------------+

    Examples
    --------

    .. code-block:: css

        HotCathodeGauge [interlocked="true"] #interlock {
            border: 5px solid red;
        }
        HotCathodeGauge [interlocked="false"] #interlock {
            border: 0px;
        }
        HotCathodeGauge [state="Error"] #icon {
            qproperty-penColor: red;
            qproperty-penWidth: 2;
        }

    """
    _interlock_suffix = ":ILK_OK"
    _state_suffix = ":STATE"
    _readback_suffix = ":PRESS"
    _command_suffix = ":HV_SW"

    Q_ENUMS(ContentLocation)
    NAME = "Hot Cathode Gauge"

    def __init__(self, parent=None, **kwargs):
        super(HotCathodeGauge, self).__init__(
            parent=parent,
            interlock_suffix=self._interlock_suffix,
            state_suffix=self._state_suffix,
            **kwargs)

        self.start_stop_btn = PyDMEnumButton()
        self.pressure_label = PyDMLabel()
        self.pressure_label.setObjectName("pressure")
        self.pressure_label.setAlignment(Qt.AlignCenter)
        self.icon = HotCathodeGaugeSymbolIcon(self)
        self.icon.setMinimumSize(16, 16)
        self.icon.setSizePolicy(QSizePolicy.Expanding,
                                QSizePolicy.Expanding)
        self.icon.setVisible(self._show_icon)
        self.iconSize = 32

        self.controls_layout = QVBoxLayout()
        self.controls_layout.setSpacing(0)
        self.controls_layout.setContentsMargins(0, 0, 0, 0)
        self.controls_frame.setLayout(self.controls_layout)
        self.controls_frame.layout().addWidget(self.pressure_label)
        self.controls_frame.layout().addWidget(self.start_stop_btn)

        self.assemble_layout()
        self.update_status_tooltip()

    @Property(ContentLocation)
    def controlsLocation(self):
        """
        Property controlling where the controls frame will be displayed.

        Returns
        -------
        location : ContentLocation
        """
        return self._controls_location

    @controlsLocation.setter
    def controlsLocation(self, location):
        """
        Property controlling where the controls frame will be displayed.

        Parameters
        ----------
        location : ContentLocation
        """
        if location != self._controls_location:
            self._controls_location = location
            self.assemble_layout()

    def sizeHint(self):
        """
        Suggested initial size for the widget.

        Returns
        -------
        size : QSize
        """
        return QSize(200, 200)

    def assemble_layout(self):
        """
        Assembles the widget's inner layout depending on the ContentLocation
        and other configurations set and adjust the orientation of the control
        button depending on the location.
        """
        super(HotCathodeGauge, self).assemble_layout()
        if self.controlsLocation in [ContentLocation.Top,
                                     ContentLocation.Bottom]:
            self.start_stop_btn.orientation = Qt.Horizontal
            self.start_stop_btn.setMinimumSize(100, 40)
        else:
            self.start_stop_btn.orientation = Qt.Vertical
            self.start_stop_btn.setMinimumSize(100, 80)

    def create_channels(self):
        """
        Method invoked when the channels associated with the widget must be
        created.
        This method also sets the channel address for the pressure label and
        control button.
        """
        super(HotCathodeGauge, self).create_channels()
        if self._channels_prefix:
            self.pressure_label.channel = "{}{}".format(self._channels_prefix,
                                                        self._readback_suffix)
            self.start_stop_btn.channel = "{}{}".format(self._channels_prefix,
                                                        self._command_suffix)

    def destroy_channels(self):
        """
        Method invoked when the channels associated with the widget must be
        destroyed.
        This method also clears the channel address for the pressure label and
        control button.
        """
        super(HotCathodeGauge, self).destroy_channels()
        self.pressure_label.channel = None
        self.start_stop_btn.channel = None

    def interlock_value_changed(self, value):
        """
        Callback invoked when the value changes for the Interlock Channel.
        This method is responsible for enabling/disabling the controls frame
        depending on the interlock status.

        Parameters
        ----------
        value : int
            The value from the channel will be either 0 or 1 with 1 meaning
            that the widget is interlocked.
        """
        InterlockMixin.interlock_value_changed(self, value)
        self.controls_frame.setEnabled(not self._interlocked)


class ColdCathodeGauge(InterlockMixin, StateMixin, PCDSSymbolBase,
                       ContentLocation):
    """
    A Symbol Widget representing a Cold Cathode Gauge with the proper icon and
    controls.

    Parameters
    ----------
    parent : QWidget
        The parent widget for the symbol

    Notes
    -----
    This widget allow for high customization through the Qt Stylesheets
    mechanism.
    As this widget is composed by internal widgets, their names can be used as
    selectors when writing your stylesheet to be used with this widget.
    Properties are also available to offer wider customization possibilities.

    **Internal Components**

    +-----------+--------------+---------------------------------------+
    |Widget Name|Type          |What is it?                            |
    +===========+==============+=======================================+
    |interlock  |QFrame        |The QFrame wrapping this whole widget. |
    +-----------+--------------+---------------------------------------+
    |controls   |QFrame        |The QFrame wrapping the controls panel.|
    +-----------+--------------+---------------------------------------+
    |icon       |BaseSymbolIcon|The widget containing the icon drawing.|
    +-----------+--------------+---------------------------------------+
    |pressure   |PyDMLabel     |The pressure reading label.            |
    +-----------+--------------+---------------------------------------+

    **Additional Properties**

    +-----------+-------------------------------------------------------------+
    |Property   |Values                                                       |
    +===========+=============================================================+
    |interlocked|`true` or `false`                                            |
    +-----------+-------------------------------------------------------------+
    |state      |`On`, `Off`, `Starting` or `Error`                           |
    +-----------+-------------------------------------------------------------+

    Examples
    --------

    .. code-block:: css

        ColdCathodeGauge [interlocked="true"] #interlock {
            border: 5px solid red;
        }
        ColdCathodeGauge [interlocked="false"] #interlock {
            border: 0px;
        }
        ColdCathodeGauge [state="Error"] #icon {
            qproperty-penColor: red;
            qproperty-penWidth: 2;
        }

    """
    _interlock_suffix = ":ILK_OK"
    _state_suffix = ":STATE"
    _readback_suffix = ":PRESS"
    _command_suffix = ":HV_SW"

    Q_ENUMS(ContentLocation)
    NAME = "Cold Cathode Gauge"

    def __init__(self, parent=None, **kwargs):
        super(ColdCathodeGauge, self).__init__(
            parent=parent,
            interlock_suffix=self._interlock_suffix,
            state_suffix=self._state_suffix,
            **kwargs)

        self.start_stop_btn = PyDMEnumButton()
        self.pressure_label = PyDMLabel()
        self.pressure_label.setObjectName("pressure")
        self.pressure_label.setAlignment(Qt.AlignCenter)
        self.icon = ColdCathodeGaugeSymbolIcon(self)
        self.icon.setMinimumSize(16, 16)
        self.icon.setSizePolicy(QSizePolicy.Expanding,
                                QSizePolicy.Expanding)
        self.icon.setVisible(self._show_icon)
        self.iconSize = 32

        self.controls_layout = QVBoxLayout()
        self.controls_layout.setSpacing(0)
        self.controls_layout.setContentsMargins(0, 0, 0, 0)
        self.controls_frame.setLayout(self.controls_layout)
        self.controls_frame.layout().addWidget(self.pressure_label)
        self.controls_frame.layout().addWidget(self.start_stop_btn)

        self.assemble_layout()
        self.update_status_tooltip()

    @Property(ContentLocation)
    def controlsLocation(self):
        """
        Property controlling where the controls frame will be displayed.

        Returns
        -------
        location : ContentLocation
        """
        return self._controls_location

    @controlsLocation.setter
    def controlsLocation(self, location):
        """
        Property controlling where the controls frame will be displayed.

        Parameters
        ----------
        location : ContentLocation
        """
        if location != self._controls_location:
            self._controls_location = location
            self.assemble_layout()

    def sizeHint(self):
        """
        Suggested initial size for the widget.

        Returns
        -------
        size : QSize
        """
        return QSize(200, 200)

    def assemble_layout(self):
        """
        Assembles the widget's inner layout depending on the ContentLocation
        and other configurations set and adjust the orientation of the control
        button depending on the location.
        """
        super(ColdCathodeGauge, self).assemble_layout()
        if self.controlsLocation in [ContentLocation.Top,
                                     ContentLocation.Bottom]:
            self.start_stop_btn.orientation = Qt.Horizontal
            self.start_stop_btn.setMinimumSize(100, 40)
        else:
            self.start_stop_btn.orientation = Qt.Vertical
            self.start_stop_btn.setMinimumSize(100, 80)

    def create_channels(self):
        """
        Method invoked when the channels associated with the widget must be
        created.
        This method also sets the channel address for the pressure label and
        control button.
        """
        super(ColdCathodeGauge, self).create_channels()
        if self._channels_prefix:
            self.pressure_label.channel = "{}{}".format(self._channels_prefix,
                                                        self._readback_suffix)
            self.start_stop_btn.channel = "{}{}".format(self._channels_prefix,
                                                        self._command_suffix)

    def destroy_channels(self):
        """
        Method invoked when the channels associated with the widget must be
        destroyed.
        This method also clears the channel address for the pressure label and
        control button.
        """
        super(ColdCathodeGauge, self).destroy_channels()
        self.pressure_label.channel = None
        self.start_stop_btn.channel = None

    def interlock_value_changed(self, value):
        """
        Callback invoked when the value changes for the Interlock Channel.
        This method is responsible for enabling/disabling the controls frame
        depending on the interlock status.

        Parameters
        ----------
        value : int
            The value from the channel will be either 0 or 1 with 1 meaning
            that the widget is interlocked.
        """
        InterlockMixin.interlock_value_changed(self, value)
        self.controls_frame.setEnabled(not self._interlocked)
