from pydm.widgets.enum_button import PyDMEnumButton
from pydm.widgets.label import PyDMLabel
from qtpy.QtCore import QSize, Qt, Property, Q_ENUMS
from qtpy.QtWidgets import QVBoxLayout, QSizePolicy

from .base import PCDSSymbolBase, ContentLocation
from .mixins import InterlockMixin, ErrorMixin, StateMixin
from ..icons.pumps import (IonPumpSymbolIcon, TurboPumpSymbolIcon,
                           ScrollPumpSymbolIcon)


class IonPump(InterlockMixin, ErrorMixin, StateMixin,
              PCDSSymbolBase, ContentLocation):
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

    +-----------+--------------+--------------------------------------------+
    |Widget Name|Type          |What is it?                                 |
    +===========+==============+============================================+
    |interlock  |QFrame        |The QFrame wrapping this whole widget.      |
    +-----------+--------------+--------------------------------------------+
    |controls   |QFrame        |The QFrame wrapping the controls panel.     |
    +-----------+--------------+--------------------------------------------+
    |icon       |BaseSymbolIcon|The widget containing the icon drawing.     |
    +-----------+--------------+--------------------------------------------+
    |pressure   |PyDMLabel     |The widget containing the pressure readback.|
    +-----------+--------------+--------------------------------------------+

    **Additional Properties**

    +-----------+-------------------------------------------------------------+
    |Property   |Values                                                       |
    +===========+=============================================================+
    |interlocked|`true` or `false`                                            |
    +-----------+-------------------------------------------------------------+
    |error      |`true` or  `false`                                           |
    +-----------+-------------------------------------------------------------+
    |state      |`On`, `Off`                                                  |
    +-----------+-------------------------------------------------------------+

    Examples
    --------

    .. code-block:: css

        IonPump [interlocked="true"] #interlock {
            border: 5px solid red;
        }
        IonPump [interlocked="false"] #interlock {
            border: 0px;
        }
        IonPump [error="true"] #icon {
            qproperty-penStyle: "Qt::DotLine";
            qproperty-penWidth: 2;
            qproperty-brush: red;
        }
        IonPump [state="On"] #icon {
            qproperty-penColor: green;
            qproperty-penWidth: 2;
        }

    """
    _interlock_suffix = ":ILK_OK"
    _error_suffix = ":ERROR"
    _state_suffix = ":HV_DO"
    Q_ENUMS(ContentLocation)
    NAME = "Ion Pump"

    def __init__(self, parent=None, **kwargs):
        super(IonPump, self).__init__(parent=parent,
                                      interlock_suffix=self._interlock_suffix,
                                      error_suffix=self._error_suffix,
                                      state_suffix=self._state_suffix,
                                      **kwargs)

        self.start_stop_btn = PyDMEnumButton()
        self.pressure_label = PyDMLabel()
        self.pressure_label.setObjectName("pressure")
        self.pressure_label.setAlignment(Qt.AlignCenter)
        self.icon = IonPumpSymbolIcon(self)
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
        super(IonPump, self).assemble_layout()
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
        super(IonPump, self).create_channels()
        if self._channels_prefix:
            self.pressure_label.channel = "{}{}".format(self._channels_prefix,
                                                        ":PRESS")
            self.start_stop_btn.channel = "{}{}".format(self._channels_prefix,
                                                        ":HV_SW")

    def destroy_channels(self):
        """
        Method invoked when the channels associated with the widget must be
        destroyed.
        This method also clears the channel address for the pressure label and
        control button.
        """
        super(IonPump, self).destroy_channels()
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


class TurboPump(InterlockMixin, ErrorMixin, StateMixin,
                PCDSSymbolBase, ContentLocation):
    """
    A Symbol Widget representing a Turbo Pump with the proper icon and
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

    **Additional Properties**

    +-----------+-------------------------------------------------------------+
    |Property   |Values                                                       |
    +===========+=============================================================+
    |interlocked|`true` or `false`                                            |
    +-----------+-------------------------------------------------------------+
    |error      |`true` or  `false`                                           |
    +-----------+-------------------------------------------------------------+
    |state      |`On`, `Accelerating` or `Off`                                |
    +-----------+-------------------------------------------------------------+

    Examples
    --------

    .. code-block:: css

        TurboPump [interlocked="true"] #interlock {
            border: 5px solid red;
        }
        TurboPump [interlocked="false"] #interlock {
            border: 0px;
        }
        TurboPump [error="true"] #icon {
            qproperty-penStyle: "Qt::DotLine";
            qproperty-penWidth: 2;
            qproperty-brush: red;
        }
        TurboPump [state="Accelerating"] #icon {
            qproperty-centerBrush: red;
        }

    """
    _interlock_suffix = ":ILK_STATUS"
    _error_suffix = ":FAULT"
    _state_suffix = ":STATE"
    Q_ENUMS(ContentLocation)
    NAME = "Turbo Pump"

    def __init__(self, parent=None, **kwargs):
        super(TurboPump, self).__init__(
            parent=parent,
            interlock_suffix=self._interlock_suffix,
            error_suffix=self._error_suffix,
            state_suffix=self._state_suffix,
            **kwargs)

        self.start_stop_btn = PyDMEnumButton()
        self.icon = TurboPumpSymbolIcon(self)
        self.icon.setMinimumSize(16, 16)
        self.icon.setSizePolicy(QSizePolicy.Expanding,
                                QSizePolicy.Expanding)
        self.icon.setVisible(self._show_icon)
        self.iconSize = 32

        self.controls_layout = QVBoxLayout()
        self.controls_layout.setSpacing(0)
        self.controls_layout.setContentsMargins(0, 0, 0, 0)
        self.controls_frame.setLayout(self.controls_layout)
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
        super(TurboPump, self).assemble_layout()
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
        This method also sets the channel address for the control button.
        """
        super(TurboPump, self).create_channels()
        if self._channels_prefix:
            self.start_stop_btn.channel = "{}{}".format(self._channels_prefix,
                                                        ":RUN_SW")

    def destroy_channels(self):
        """
        Method invoked when the channels associated with the widget must be
        destroyed.
        This method also clears the channel address for the control button.
        """
        super(TurboPump, self).destroy_channels()
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


class ScrollPump(InterlockMixin, ErrorMixin, StateMixin,
                 PCDSSymbolBase, ContentLocation):
    """
    A Symbol Widget representing a Scroll Pump with the proper icon and
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

    **Additional Properties**

    +-----------+-------------------------------------------------------------+
    |Property   |Values                                                       |
    +===========+=============================================================+
    |interlocked|`true` or `false`                                            |
    +-----------+-------------------------------------------------------------+
    |error      |`true` or  `false`                                           |
    +-----------+-------------------------------------------------------------+
    |state      |`On`, `Accelerating` or `Off`                                |
    +-----------+-------------------------------------------------------------+

    Examples
    --------

    .. code-block:: css

        ScrollPump [interlocked="true"] #interlock {
            border: 5px solid red;
        }
        ScrollPump [interlocked="false"] #interlock {
            border: 0px;
        }
        ScrollPump [error="true"] #icon {
            qproperty-penStyle: "Qt::DotLine";
            qproperty-penWidth: 2;
            qproperty-brush: red;
        }
        ScrollPump [state="Accelerating"] #icon {
            qproperty-centerBrush: red;
        }

    """
    _interlock_suffix = ":ILK_OK"
    _error_suffix = ":ERROR"
    _state_suffix = ":STATE"
    Q_ENUMS(ContentLocation)
    NAME = "Scroll Pump"

    def __init__(self, parent=None, **kwargs):
        super(ScrollPump, self).__init__(
            parent=parent,
            interlock_suffix=self._interlock_suffix,
            error_suffix=self._error_suffix,
            state_suffix=self._state_suffix,
            **kwargs)

        self.start_stop_btn = PyDMEnumButton()
        self.icon = ScrollPumpSymbolIcon(self)
        self.icon.setMinimumSize(16, 16)
        self.icon.setSizePolicy(QSizePolicy.Expanding,
                                QSizePolicy.Expanding)
        self.icon.setVisible(self._show_icon)
        self.iconSize = 32

        self.controls_layout = QVBoxLayout()
        self.controls_layout.setSpacing(0)
        self.controls_layout.setContentsMargins(0, 0, 0, 0)
        self.controls_frame.setLayout(self.controls_layout)
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
        super(ScrollPump, self).assemble_layout()
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
        This method also sets the channel address for the control button.
        """
        super(ScrollPump, self).create_channels()
        if self._channels_prefix:
            self.start_stop_btn.channel = "{}{}".format(self._channels_prefix,
                                                        ":RUN_SW")

    def destroy_channels(self):
        """
        Method invoked when the channels associated with the widget must be
        destroyed.
        This method also clears the channel address for the control button.
        """
        super(ScrollPump, self).destroy_channels()
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
