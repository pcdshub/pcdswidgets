from qtpy.QtCore import QSize, Property

from .base import PCDSSymbolBase, ContentLocation
from .mixins import (InterlockMixin, ErrorMixin, OpenCloseStateMixin,
                     StateMixin, ButtonControl)
from ..icons.valves import (ApertureValveSymbolIcon, PneumaticValveSymbolIcon,
                            FastShutterSymbolIcon, NeedleValveSymbolIcon,
                            ProportionalValveSymbolIcon,
                            RightAngleManualValveSymbolIcon,
                            ControlValveSymbolIcon,
                            ControlOnlyValveSymbolIcon)


class PneumaticValve(InterlockMixin, ErrorMixin, OpenCloseStateMixin,
                     ButtonControl, PCDSSymbolBase):
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
    |state      |`Open`, `Close` or `INVALID`                           |
    +-----------+-------------------------------------------------------+

    Examples
    --------

    .. code-block:: css

        PneumaticValve [interlocked="true"] #interlock {
            border: 5px solid red;
        }
        PneumaticValve [interlocked="false"] #interlock {
            border: 0px;
        }
        PneumaticValve [interlocked="true"] #icon {
            qproperty-interlockBrush: #FF0000;
        }
        PneumaticValve [interlocked="false"] #icon {
            qproperty-interlockBrush: #00FF00;
        }
        PneumaticValve [error="Lost Vacuum"] #icon {
            qproperty-penStyle: "Qt::DotLine";
            qproperty-penWidth: 2;
            qproperty-brush: red;
        }
        PneumaticValve [state="Open"] #icon {
            qproperty-penColor: green;
            qproperty-penWidth: 2;
        }

    """
    _interlock_suffix = ":OPN_OK_RBV"
    _error_suffix = ":STATE_RBV"
    _open_state_suffix = ":OPN_DI_RBV"
    _close_state_suffix = ":CLS_DI_RBV"
    _command_suffix = ":OPN_SW"

    NAME = "Pneumatic Valve"

    def __init__(self, parent=None, **kwargs):
        self.icon = PneumaticValveSymbolIcon()
        super(PneumaticValve, self).__init__(
            parent=parent,
            interlock_suffix=self._interlock_suffix,
            error_suffix=self._error_suffix,
            open_suffix=self._open_state_suffix,
            close_suffix=self._close_state_suffix,
            command_suffix=self._command_suffix,
            **kwargs)

    def sizeHint(self):
        return QSize(180, 70)


class ApertureValve(InterlockMixin, ErrorMixin, OpenCloseStateMixin,
                    ButtonControl, PCDSSymbolBase):
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
    |state      |`Open`, `Close` or `INVALID`                           |
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
    _interlock_suffix = ":OPN_OK_RBV"
    _error_suffix = ":STATE_RBV"
    _open_state_suffix = ":OPN_DI_RBV"
    _close_state_suffix = ":CLS_DI_RBV"
    _command_suffix = ":OPN_SW"

    NAME = "Aperture Valve"

    def __init__(self, parent=None, **kwargs):
        self.icon = ApertureValveSymbolIcon()
        super(ApertureValve, self).__init__(
            parent=parent,
            interlock_suffix=self._interlock_suffix,
            error_suffix=self._error_suffix,
            open_suffix=self._open_state_suffix,
            close_suffix=self._close_state_suffix,
            command_suffix=self._command_suffix,
            **kwargs)

    def sizeHint(self):
        return QSize(180, 70)


class FastShutter(InterlockMixin, ErrorMixin, OpenCloseStateMixin,
                  ButtonControl, PCDSSymbolBase):
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
    |state      |`Open`, `Close` or `INVALID`                                 |
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
        }
        FastShutter [state="Open"] #icon {
            qproperty-penColor: green;
            qproperty-penWidth: 2;
        }

    """
    _interlock_suffix = ":VAC_FAULT_OK_RBV"
    _error_suffix = ":ERROR_RBV"
    _open_state_suffix = ":OPN_DI_RBV"
    _close_state_suffix = ":CLS_DI_RBV"
    _command_suffix = ":OPN_SW"

    NAME = "Fast Shutter"

    def __init__(self, parent=None, **kwargs):
        self.icon = FastShutterSymbolIcon()
        super(FastShutter, self).__init__(
            parent=parent,
            interlock_suffix=self._interlock_suffix,
            error_suffix=self._error_suffix,
            open_suffix=self._open_state_suffix,
            close_suffix=self._close_state_suffix,
            command_suffix=self._command_suffix,
            **kwargs)

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
    _interlock_suffix = ":ILK_OK_RBV"
    _state_suffix = ":STATE_RBV"
    _command_suffix = ":OPN_SW"

    NAME = "Needle Valve"

    def __init__(self, parent=None, **kwargs):
        self.icon = NeedleValveSymbolIcon()
        super(NeedleValve, self).__init__(
            parent=parent,
            interlock_suffix=self._interlock_suffix,
            state_suffix=self._state_suffix,
            command_suffix=self._command_suffix,
            **kwargs)

    def sizeHint(self):
        return QSize(180, 70)


class ProportionalValve(InterlockMixin, StateMixin, ButtonControl,
                        PCDSSymbolBase):
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
    _interlock_suffix = ":ILK_OK_RBV"
    _state_suffix = ":STATE_RBV"
    _command_suffix = ":OPN_SW"

    NAME = "Proportional Valve"

    def __init__(self, parent=None, **kwargs):
        self.icon = ProportionalValveSymbolIcon()
        super(ProportionalValve, self).__init__(
            parent=parent,
            interlock_suffix=self._interlock_suffix,
            state_suffix=self._state_suffix,
            command_suffix=self._command_suffix,
            **kwargs)

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
    NAME = "Right Angle Manual Valve"

    def __init__(self, parent=None, **kwargs):
        self.icon = RightAngleManualValveSymbolIcon()
        self._controls_location = ContentLocation.Hidden
        super(RightAngleManualValve, self).__init__(parent=parent, **kwargs)

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


class ControlValve(InterlockMixin, ErrorMixin, OpenCloseStateMixin,
                   ButtonControl, PCDSSymbolBase):
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
    |state      |`Open`, `Close` or `INVALID`                           |
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
    NAME = 'Control Valve with Readback'
    _interlock_suffix = ":OPN_OK_RBV"
    _error_suffix = ":STATE_RBV"
    _open_state_suffix = ":OPN_DI_RBV"
    _close_state_suffix = ":CLS_DI_RBV"
    _command_suffix = ":OPN_SW"

    def __init__(self, parent=None, **kwargs):
        self.icon = ControlValveSymbolIcon()
        super().__init__(
            parent=parent,
            interlock_suffix=self._interlock_suffix,
            error_suffix=self._error_suffix,
            open_suffix=self._open_state_suffix,
            close_suffix=self._close_state_suffix,
            command_suffix=self._command_suffix,
            **kwargs)

    def sizeHint(self):
        return QSize(180, 70)


class ControlOnlyValveNC(InterlockMixin, StateMixin,
                         ButtonControl, PCDSSymbolBase):
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
    NAME = 'Normally Closed Control Valve with No Readback'
    _interlock_suffix = ":OPN_OK_RBV"
    _state_suffix = ':OPN_DO_RBV'
    _command_suffix = ":OPN_SW"

    def __init__(self, parent=None, **kwargs):
        self.icon = ControlOnlyValveSymbolIcon()
        super().__init__(
            parent=parent,
            interlock_suffix=self._interlock_suffix,
            state_suffix=self._state_suffix,
            command_suffix=self._command_suffix,
            **kwargs)

    def sizeHint(self):
        return QSize(180, 70)


class ControlOnlyValveNO(InterlockMixin, StateMixin,
                         ButtonControl, PCDSSymbolBase):
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
    NAME = 'Normally Open Control Valve with No Readback'
    _interlock_suffix = ":CLS_OK_RBV"
    _state_suffix = ':CLS_DO_RBV'
    _command_suffix = ":CLS_SW"

    def __init__(self, parent=None, **kwargs):
        self.icon = ControlOnlyValveSymbolIcon()
        super().__init__(
            parent=parent,
            interlock_suffix=self._interlock_suffix,
            state_suffix=self._state_suffix,
            command_suffix=self._command_suffix,
            **kwargs)
