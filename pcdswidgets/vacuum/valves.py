from pydm.widgets.channel import PyDMChannel
from pydm.widgets.pushbutton import PyDMPushButton
from qtpy.QtCore import Property, QSize, Qt
from qtpy.QtWidgets import QGridLayout

from ..icons.valves import (ApertureValveSymbolIcon,
                            ControlOnlyValveSymbolIcon, ControlValveSymbolIcon,
                            FastShutterSymbolIcon, NeedleValveSymbolIcon,
                            PneumaticValveDASymbolIcon,
                            PneumaticValveNOSymbolIcon,
                            PneumaticValveSymbolIcon,
                            ProportionalValveSymbolIcon,
                            RightAngleManualValveSymbolIcon)
from .base import ContentLocation, PCDSSymbolBase
from .mixins import (ButtonControl, ErrorMixin, InterlockMixin,
                     MultipleButtonControl, StateMixin)


class PneumaticValve(
    InterlockMixin, ErrorMixin, StateMixin, ButtonControl, PCDSSymbolBase
):
    """
    A Symbol Widget representing a Pneumatic Valve with the proper icon and
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

    +-----------+-------------------------------------------------------+
    |Property   |Values                                                 |
    +===========+=======================================================+
    |interlocked|`true` or `false`                                      |
    +-----------+-------------------------------------------------------+
    |error      |`Vented`, `At Vacuum`, `Differential Pressure` or      |
    |           |`Lost Vacuum`                                          |
    +-----------+-------------------------------------------------------+
    |state      |`Open`, `Closed`, `Moving`, `Invalid`                  |
    +-----------+-------------------------------------------------------+

    Examples
    --------

    .. code-block:: css

        PneumaticValve[interlocked="true"] #interlock {
            border: 5px solid red;
        }
        PneumaticValve[interlocked="false"] #interlock {
            border: 0px;
        }
        PneumaticValve[interlocked="true"] #icon {
            qproperty-interlockBrush: #FF0000;
        }
        PneumaticValve[interlocked="false"] #icon {
            qproperty-interlockBrush: #00FF00;
        }
        PneumaticValve[error="Lost Vacuum"] #icon {
            qproperty-penStyle: "Qt::DotLine";
            qproperty-penWidth: 2;
            qproperty-brush: red;
        }
        PneumaticValve[state="Open"] #icon {
            qproperty-penColor: green;
            qproperty-penWidth: 2;
        }

    """

    _qt_designer_ = {
        "group": "PCDS Valves",
        "is_container": False,
    }

    _interlock_suffix = ":OPN_OK_RBV"
    _error_suffix = ":STATE_RBV"
    _state_suffix = ":POS_STATE_RBV"
    _command_suffix = ":OPN_SW"

    NAME = "Pneumatic Valve"
    EXPERT_OPHYD_CLASS = "pcdsdevices.valve.VGC"

    def __init__(self, parent=None, **kwargs):
        super().__init__(
            parent=parent,
            interlock_suffix=self._interlock_suffix,
            error_suffix=self._error_suffix,
            state_suffix=self._state_suffix,
            command_suffix=self._command_suffix,
            **kwargs)
        self.icon = PneumaticValveSymbolIcon(parent=self)

    def sizeHint(self):
        return QSize(180, 70)


class ApertureValve(
    InterlockMixin, ErrorMixin, StateMixin, ButtonControl, PCDSSymbolBase
):
    """
    A Symbol Widget representing an Aperture Valve with the proper icon and
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

    +-----------+-------------------------------------------------------+
    |Property   |Values                                                 |
    +===========+=======================================================+
    |interlocked|`true` or `false`                                      |
    +-----------+-------------------------------------------------------+
    |error      |`Vented`, `At Vacuum`, `Differential Pressure` or      |
    |           |`Lost Vacuum`                                          |
    +-----------+-------------------------------------------------------+
    |state      |`Open`, `Close`, `Moving` or `INVALID`                 |
    +-----------+-------------------------------------------------------+

    Examples
    --------

    .. code-block:: css

        ApertureValve [interlocked="true"] #interlock {
            border: 5px solid red;
        }
        ApertureValve [interlocked="false"] #interlock {
            border: 0px;
        }
        ApertureValve [interlocked="true"] #icon {
            qproperty-interlockBrush: #FF0000;
        }
        ApertureValve [interlocked="false"] #icon {
            qproperty-interlockBrush: #00FF00;
        }
        ApertureValve [error="Lost Vacuum"] #icon {
            qproperty-penStyle: "Qt::DotLine";
            qproperty-penWidth: 2;
            qproperty-brush: red;
        }
        ApertureValve [state="Open"] #icon {
            qproperty-penColor: green;
            qproperty-penWidth: 2;
        }

    """

    _qt_designer_ = {
        "group": "PCDS Valves",
        "is_container": False,
    }
    _interlock_suffix = ":OPN_OK_RBV"
    _error_suffix = ":STATE_RBV"
    _state_suffix = ":POS_STATE_RBV"
    _command_suffix = ":OPN_SW"

    NAME = "Aperture Valve"
    EXPERT_OPHYD_CLASS = "pcdsdevices.valve.VRC"

    def __init__(self, parent=None, **kwargs):
        super().__init__(
            parent=parent,
            interlock_suffix=self._interlock_suffix,
            error_suffix=self._error_suffix,
            state_suffix=self._state_suffix,
            command_suffix=self._command_suffix,
            **kwargs)
        self.icon = ApertureValveSymbolIcon(parent=self)

    def sizeHint(self):
        return QSize(180, 70)


class FastShutter(
    InterlockMixin, ErrorMixin, StateMixin, MultipleButtonControl, PCDSSymbolBase
):
    """
    A Symbol Widget representing a Fast Shutter with the proper icon and
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
    |error      |`true`, or `false`                                           |
    +-----------+-------------------------------------------------------------+
    |state      |`Open`, `Close` `Moving` or `INVALID`                        |
    +-----------+-------------------------------------------------------------+

    Examples
    --------

    .. code-block:: css

        FastShutter [interlocked="true"] #interlock {
            border: 5px solid red;
        }
        FastShutter [interlocked="false"] #interlock {
            border: 0px;
        }
        FastShutter [error="true"] #icon {
            qproperty-penStyle: "Qt::DotLine";
            qproperty-penWidth: 2;
            qproperty-brush: red;
            qproperty-arrowBrush: #00FF00;
        }
        FastShutter [state="Open"] #icon {
            qproperty-penColor: green;
            qproperty-penWidth: 2;
        }

    """

    _qt_designer_ = {
        "group": "PCDS Valves",
        "is_container": False,
    }
    _interlock_suffix = ":OPN_OK_RBV"
    _error_suffix = ":STATE_RBV"
    _state_suffix = ":POS_STATE_RBV"
    _command_buttons = [
        {"suffix": ":OPN_SW", "text": "OPEN", "value": 1},
        {"suffix": ":CLS_SW", "text": "CLOSE", "value": 1},
    ]

    NAME = "Fast Shutter"
    EXPERT_OPHYD_CLASS = "pcdsdevices.valve.VFS"

    def __init__(self, parent=None, **kwargs):
        super().__init__(
            parent=parent,
            interlock_suffix=self._interlock_suffix,
            error_suffix=self._error_suffix,
            state_suffix=self._state_suffix,
            commands=self._command_buttons,
            **kwargs)
        self.icon = FastShutterSymbolIcon(parent=self)

    def sizeHint(self):
        return QSize(180, 70)


class NeedleValve(InterlockMixin, StateMixin, ButtonControl, PCDSSymbolBase):
    """
    A Symbol Widget representing a Needle Valve with the proper icon and
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
    |state      |`Close`, `Open`, `PressureControl`, `ManualControl`          |
    +-----------+-------------------------------------------------------------+

    Examples
    --------

    .. code-block:: css

        NeedleValve [interlocked="true"] #interlock {
            border: 5px solid red;
        }
        NeedleValve [interlocked="false"] #interlock {
            border: 0px;
        }
        FastShutter [state="Open"] #icon {
            qproperty-penColor: green;
            qproperty-penWidth: 2;
        }

    """

    _qt_designer_ = {
        "group": "PCDS Valves",
        "is_container": False,
    }
    _interlock_suffix = ":ILK_OK_RBV"
    _state_suffix = ":STATE_RBV"
    _command_suffix = ":OPN_SW"

    NAME = "Needle Valve"
    EXPERT_OPHYD_CLASS = "pcdsdevices.valve.VCN"

    def __init__(self, parent=None, **kwargs):
        super().__init__(
            parent=parent,
            interlock_suffix=self._interlock_suffix,
            state_suffix=self._state_suffix,
            command_suffix=self._command_suffix,
            **kwargs)
        self.icon = NeedleValveSymbolIcon(parent=self)

    def sizeHint(self):
        return QSize(180, 70)


class ProportionalValve(InterlockMixin, StateMixin, ButtonControl, PCDSSymbolBase):
    """
    A Symbol Widget representing a Proportional Valve with the proper icon and
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
    |state      |`Close`, `Open`, `PressureControl`, `ManualControl`          |
    +-----------+-------------------------------------------------------------+

    Examples
    --------

    .. code-block:: css

        ProportionalValve [interlocked="true"] #interlock {
            border: 5px solid red;
        }
        ProportionalValve [interlocked="false"] #interlock {
            border: 0px;
        }
        ProportionalValve [state="Open"] #icon {
            qproperty-penColor: green;
            qproperty-penWidth: 2;
        }

    """

    _qt_designer_ = {
        "group": "PCDS Valves",
        "is_container": False,
    }
    _interlock_suffix = ":ILK_OK_RBV"
    _state_suffix = ":STATE_RBV"
    _command_suffix = ":OPN_SW"

    NAME = "Proportional Valve"
    EXPERT_OPHYD_CLASS = "pcdsdevices.valve.VRC"

    def __init__(self, parent=None, **kwargs):
        super().__init__(
            parent=parent,
            interlock_suffix=self._interlock_suffix,
            state_suffix=self._state_suffix,
            command_suffix=self._command_suffix,
            **kwargs)
        self.icon = ProportionalValveSymbolIcon(parent=self)

    def sizeHint(self):
        return QSize(180, 70)


class RightAngleManualValve(PCDSSymbolBase):
    """
    A Symbol Widget representing a Right Angle Manual Valve with the proper
    icon.

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

    """

    _qt_designer_ = {
        "group": "PCDS Valves",
        "is_container": False,
    }
    NAME = "Right Angle Manual Valve"

    def __init__(self, parent=None, **kwargs):
        self._controls_location = ContentLocation.Hidden
        super().__init__(parent=parent, **kwargs)
        self.icon = RightAngleManualValveSymbolIcon(parent=self)

    def sizeHint(self):
        """
        Suggested initial size for the widget.

        Returns
        -------
        size : QSize
        """
        return QSize(40, 40)

    @Property(str, designable=False)
    def channelsPrefix(self):
        return super().channelsPrefix

    @Property(bool, designable=False)
    def showIcon(self):
        return super().showIcon

    @Property(ContentLocation, designable=False)
    def controlsLocation(self):
        return super().controlsLocation


class ControlValve(
    InterlockMixin, ErrorMixin, StateMixin, ButtonControl, PCDSSymbolBase
):
    """
    A Symbol Widget representing a Control Valve with the proper icon and
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

    +-----------+-------------------------------------------------------+
    |Property   |Values                                                 |
    +===========+=======================================================+
    |interlocked|`true` or `false`                                      |
    +-----------+-------------------------------------------------------+
    |error      |`Vented`, `At Vacuum`, `Differential Pressure` or      |
    |           |`Lost Vacuum`                                          |
    +-----------+-------------------------------------------------------+
    |state      |`Open`, `Close` `Moving` or `INVALID`                  |
    +-----------+-------------------------------------------------------+

    Examples
    --------

    .. code-block:: css

        ControlValve [interlocked="true"] #interlock {
            border: 5px solid red;
        }
        ControlValve [interlocked="false"] #interlock {
            border: 0px;
        }
        ControlValve [interlocked="true"] #icon {
            qproperty-interlockBrush: #FF0000;
        }
        ControlValve [interlocked="false"] #icon {
            qproperty-interlockBrush: #00FF00;
        }
        ControlValve [error="Lost Vacuum"] #icon {
            qproperty-penStyle: "Qt::DotLine";
            qproperty-penWidth: 2;
            qproperty-brush: red;
        }
        ControlValve [state="Open"] #icon {
            qproperty-penColor: green;
            qproperty-penWidth: 2;
        }

    """

    _qt_designer_ = {
        "group": "PCDS Valves",
        "is_container": False,
    }
    NAME = 'Control Valve with Readback'
    EXPERT_OPHYD_CLASS = "pcdsdevices.valve.VVC"

    _interlock_suffix = ":OPN_OK_RBV"
    _error_suffix = ":STATE_RBV"
    _state_suffix = ":POS_STATE_RBV"
    _command_suffix = ":OPN_SW"

    def __init__(self, parent=None, **kwargs):
        super().__init__(
            parent=parent,
            interlock_suffix=self._interlock_suffix,
            error_suffix=self._error_suffix,
            state_suffix=self._state_suffix,
            command_suffix=self._command_suffix,
            **kwargs)
        self.icon = ControlValveSymbolIcon(parent=self)

    def sizeHint(self):
        return QSize(180, 70)


class ControlOnlyValveNC(InterlockMixin, StateMixin, ButtonControl, PCDSSymbolBase):
    """
    A Symbol Widget representing a Normally Closed Control Valve with the
    proper icon and controls.

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

    +-----------+-------------------------------------------------------+
    |Property   |Values                                                 |
    +===========+=======================================================+
    |interlocked|`true` or `false`                                      |
    +-----------+-------------------------------------------------------+
    |state      |`Open`, `Close` or `INVALID`                           |
    +-----------+-------------------------------------------------------+

    Examples
    --------

    .. code-block:: css

        ControlOnlyValveNC [interlocked="true"] #interlock {
            border: 5px solid red;
        }
        ControlOnlyValveNC [interlocked="false"] #interlock {
            border: 0px;
        }
        ControlOnlyValveNC [interlocked="true"] #icon {
            qproperty-interlockBrush: #FF0000;
        }
        ControlOnlyValveNC [interlocked="false"] #icon {
            qproperty-interlockBrush: #00FF00;
        }
        ControlOnlyValveNC [error="Lost Vacuum"] #icon {
            qproperty-penStyle: "Qt::DotLine";
            qproperty-penWidth: 2;
            qproperty-brush: red;
        }
        ControlOnlyValveNC [state="Open"] #icon {
            qproperty-penColor: green;
            qproperty-penWidth: 2;
        }

    """

    _qt_designer_ = {
        "group": "PCDS Valves",
        "is_container": False,
    }
    NAME = 'Normally Closed Control Valve with No Readback'
    EXPERT_OPHYD_CLASS = "pcdsdevices.valve.VVC"

    _interlock_suffix = ":OPN_OK_RBV"
    _state_suffix = ':OPN_DO_RBV'
    _command_suffix = ":OPN_SW"

    def __init__(self, parent=None, **kwargs):
        super().__init__(
            parent=parent,
            interlock_suffix=self._interlock_suffix,
            state_suffix=self._state_suffix,
            command_suffix=self._command_suffix,
            **kwargs)
        self.icon = ControlOnlyValveSymbolIcon(parent=self)

    def sizeHint(self):
        return QSize(180, 70)


class ControlOnlyValveNO(InterlockMixin, StateMixin, ButtonControl, PCDSSymbolBase):
    """
    A Symbol Widget representing a Normally Open Control Valve with the
    proper icon and controls.

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

    +-----------+-------------------------------------------------------+
    |Property   |Values                                                 |
    +===========+=======================================================+
    |interlocked|`true` or `false`                                      |
    +-----------+-------------------------------------------------------+
    |state      |`Open`, `Close` or `INVALID`                           |
    +-----------+-------------------------------------------------------+

    Examples
    --------

    .. code-block:: css

        ControlOnlyValveNO [interlocked="true"] #interlock {
            border: 5px solid red;
        }
        ControlOnlyValveNO [interlocked="false"] #interlock {
            border: 0px;
        }
        ControlOnlyValveNO [interlocked="true"] #icon {
            qproperty-interlockBrush: #FF0000;
        }
        ControlOnlyValveNO [interlocked="false"] #icon {
            qproperty-interlockBrush: #00FF00;
        }
        ControlOnlyValveNO [error="Lost Vacuum"] #icon {
            qproperty-penStyle: "Qt::DotLine";
            qproperty-penWidth: 2;
            qproperty-brush: red;
        }
        ControlOnlyValveNO [state="Open"] #icon {
            qproperty-penColor: green;
            qproperty-penWidth: 2;
        }

    """

    _qt_designer_ = {
        "group": "PCDS Valves",
        "is_container": False,
    }
    NAME = 'Normally Open Control Valve with No Readback'
    EXPERT_OPHYD_CLASS = "pcdsdevices.valve.VVCNO"

    _interlock_suffix = ":CLS_OK_RBV"
    _state_suffix = ':CLS_DO_RBV'
    _command_suffix = ":CLS_SW"

    def __init__(self, parent=None, **kwargs):
        super().__init__(
            parent=parent,
            interlock_suffix=self._interlock_suffix,
            state_suffix=self._state_suffix,
            command_suffix=self._command_suffix,
            **kwargs)
        self.icon = ControlOnlyValveSymbolIcon(parent=self)


class PneumaticValveNO(
    InterlockMixin, ErrorMixin, StateMixin, ButtonControl, PCDSSymbolBase
):
    """
    A Symbol Widget representing a Normally Open Pneumatic Valve with the
    proper icon and controls.

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

    +-----------+-------------------------------------------------------+
    |Property   |Values                                                 |
    +===========+=======================================================+
    |interlocked|`true` or `false`                                      |
    +-----------+-------------------------------------------------------+
    |error      |`Vented`, `At Vacuum`, `Differential Pressure` or      |
    |           |`Lost Vacuum`                                          |
    +-----------+-------------------------------------------------------+
    |state      |`OPEN`, `CLOSED`, `MOVING`, `INVALID`                  |
    +-----------+-------------------------------------------------------+

    Examples
    --------

    .. code-block:: css

        PneumaticValveNO[interlocked="true"] #interlock {
            border: 5px solid red;
        }
        PneumaticValveNO[interlocked="false"] #interlock {
            border: 0px;
        }
        PneumaticValveNO[interlocked="true"] #icon {
            qproperty-interlockBrush: #FF0000;
        }
        PneumaticValveNO[interlocked="false"] #icon {
            qproperty-interlockBrush: #00FF00;
        }
        PneumaticValveNO[error="Lost Vacuum"] #icon {
            qproperty-penStyle: "Qt::DotLine";
            qproperty-penWidth: 2;
            qproperty-brush: red;
        }
        PneumaticValveNO[state="OPEN"] #icon {
            qproperty-penColor: green;
            qproperty-penWidth: 2;
        }

    """

    _qt_designer_ = {
        "group": "PCDS Valves",
        "is_container": False,
    }
    _interlock_suffix = ":CLS_OK_RBV"
    _error_suffix = ":STATE_RBV"
    _state_suffix = ":POS_STATE_RBV"
    _command_suffix = ":CLS_SW"

    NAME = "Pneumatic Valve NO"
    EXPERT_OPHYD_CLASS = "pcdsdevices.valve.VVCNO"

    def __init__(self, parent=None, **kwargs):
        super().__init__(
            parent=parent,
            interlock_suffix=self._interlock_suffix,
            error_suffix=self._error_suffix,
            state_suffix=self._state_suffix,
            command_suffix=self._command_suffix,
            **kwargs)
        self.icon = PneumaticValveNOSymbolIcon(parent=self)

    def sizeHint(self):
        return QSize(180, 70)


class PneumaticValveDA(InterlockMixin, ErrorMixin, StateMixin, PCDSSymbolBase):
    """
    A Symbol Widget representing a dual-acting Pneumatic Valve with
    the proper icon and controls.

    This needs to modify the normal interlock logic because it has
    two interlock PVs instead of one.

    This also needs to completely re-implement the button control
    logic because it needs to have separate PVs for opening and
    closing the valve, and the ButtonControl mixin assumes one
    PV with enum values.

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

    +-----------+-------------------------------------------------------+
    |Property   |Values                                                 |
    +===========+=======================================================+
    |interlocked|`true` or `false`                                      |
    +-----------+-------------------------------------------------------+
    |error      |`Vented`, `At Vacuum`, `Differential Pressure` or      |
    |           |`Lost Vacuum`                                          |
    +-----------+-------------------------------------------------------+
    |state      |`Open`, `Closed`, `Moving`, `Invalid`                  |
    +-----------+-------------------------------------------------------+

    Examples
    --------

    .. code-block:: css

        PneumaticValveDA[interlocked="true"] #interlock {
            border: 5px solid red;
        }
        PneumaticValveDA[interlocked="false"] #interlock {
            border: 0px;
        }
        PneumaticValveDA[interlocked="true"] #icon {
            qproperty-interlockBrush: #FF0000;
        }
        PneumaticValveDA[interlocked="false"] #icon {
            qproperty-interlockBrush: #00FF00;
        }
        PneumaticValveDA[error="Lost Vacuum"] #icon {
            qproperty-penStyle: "Qt::DotLine";
            qproperty-penWidth: 2;
            qproperty-brush: red;
        }
        PneumaticValveDA[state="Open"] #icon {
            qproperty-penColor: green;
            qproperty-penWidth: 2;
        }
    """

    _qt_designer_ = {
        "group": "PCDS Valves",
        "is_container": False,
    }
    _interlock_suffix = ":OPN_OK_RBV"
    _cls_interlock_suffix = ":CLS_OK_RBV"
    _error_suffix = ":STATE_RBV"
    _state_suffix = ":POS_STATE_RBV"
    _open_command_suffix = ":OPN_SW"
    _close_command_suffix = ":CLS_SW"

    NAME = "Pneumatic Valve DA"
    EXPERT_OPHYD_CLASS = "pcdsdevices.valve.VRCDA"

    def __init__(self, parent=None, **kwargs):
        self._cls_interlocked = False
        self._cls_interlock_connected = False
        self.cls_interlock_channel = None
        self.controls_layout = None
        super().__init__(
            parent=parent,
            interlock_suffix=self._interlock_suffix,
            error_suffix=self._error_suffix,
            state_suffix=self._state_suffix,
            **kwargs)
        self.icon = PneumaticValveDASymbolIcon(parent=self)
        self.open_btn = PyDMPushButton(
            label='OPEN',
            pressValue=1,
        )
        self.cls_btn = PyDMPushButton(
            label='CLOSE',
            pressValue=1,
        )
        self.open_btn.setFixedSize(55, 25)
        self.cls_btn.setFixedSize(55, 25)
        self.controls_layout = QGridLayout()
        self.controls_layout.setSpacing(6)
        self.controls_layout.setContentsMargins(5, 5, 5, 5)
        self.controls_frame.setLayout(self.controls_layout)
        self.controlButtonHorizontal = True

    @Property(bool, designable=False)
    def interlocked(self):
        """
        Property used to query interlock state.

        Returns
        -------
        bool
        """
        return self._interlocked or self._cls_interlocked

    @Property(bool)
    def controlButtonHorizontal(self):
        return self._orientation == Qt.Horizontal

    @controlButtonHorizontal.setter
    def controlButtonHorizontal(self, checked):
        if checked:
            self._orientation = Qt.Horizontal
        else:
            self._orientation = Qt.Vertical

        self.rearrange_button_layout()

    def rearrange_button_layout(self):
        if self._orientation == Qt.Horizontal:
            self.controls_frame.layout().addWidget(self.open_btn, 0, 1)
            self.controls_frame.layout().addWidget(self.cls_btn, 0, 0)
        else:
            self.controls_frame.layout().addWidget(self.cls_btn, 1, 0)
            self.controls_frame.layout().addWidget(self.open_btn, 0, 0)

    def create_channels(self):
        """
        Add a second interlock channel and the button channels.

        The second interlock channel is used to check if the closing
        action of the valve is permitted.

        The button channels allow us to open and close the valves.
        """
        super().create_channels()

        self._cls_interlocked = True
        self._cls_interlock_connected = False

        self.cls_interlock_channel = PyDMChannel(
            address="{}{}".format(self._channels_prefix,
                                  self._cls_interlock_suffix),
            connection_slot=self.cls_interlock_connection_changed,
            value_slot=self.cls_interlock_value_changed
        )
        self.cls_interlock_channel.connect()

        self.open_btn.channel = "{}{}".format(
            self._channels_prefix,
            self._open_command_suffix,
        )
        self.cls_btn.channel = "{}{}".format(
            self._channels_prefix,
            self._close_command_suffix,
        )

    def destroy_channels(self):
        """
        Method invoked when the channels associated with the widget must be
        destroyed.
        This method also clears the channel address for the control buttons
        and close interlock.
        """
        if self.cls_interlock_channel is not None:
            self.cls_interlock_channel.disconnect()
        self.cls_interlock_channel = None
        self.open_btn.channel = None
        self.cls_btn.channel = None

    def cls_interlock_connection_changed(self, conn):
        """
        Callback invoked when the connection status changes for the Interlock
        Channel.

        Neither this nor the open interlock connection state are currently
        used, but this was included for completeness.

        Parameters
        ----------
        conn : bool
            True if connected, False otherwise.
        """
        self._cls_interlock_connected = conn

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
        self.open_btn.setEnabled(not self._interlocked)
        self.update_da_interlock()

    def cls_interlock_value_changed(self, value):
        """
        Callback invoked when the value changes for the Interlock Channel.

        Parameters
        ----------
        value : int
            The value from the channel will be either 0 or 1 with 0 meaning
            that the widget is interlocked.
        """
        self._cls_interlocked = value == 0
        self.cls_btn.setEnabled(not self._cls_interlocked)
        self.update_da_interlock()

    def update_da_interlock(self):
        """
        Update the double-acting interlock state when either pv changes.
        """
        self.update_stylesheet()
        self.update_status_tooltip()

    def sizeHint(self):
        return QSize(180, 70)
