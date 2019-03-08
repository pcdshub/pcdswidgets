from qtpy.QtCore import QSize, Property

from .base import PCDSSymbolBase, ContentLocation
from .mixins import (InterlockMixin, ErrorMixin, OpenCloseStateMixin,
                     StateMixin, ButtonControl)
from ..icons.valves import (ApertureValveSymbolIcon, PneumaticValveSymbolIcon,
                            FastShutterSymbolIcon, NeedleValveSymbolIcon,
                            ProportionalValveSymbolIcon,
                            RightAngleManualValveSymbolIcon)


class PneumaticValve(InterlockMixin, ErrorMixin, OpenCloseStateMixin,
                     PCDSSymbolBase):
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
    _interlock_suffix = ":OPN_OK"
    _error_suffix = ":STATE"
    _open_state_suffix = ":OPN_DI"
    _close_state_suffix = ":CLS_DI"
    _command_suffix = ":OPN_SW"

    NAME = "Pneumatic Valve"

    def __init__(self, parent=None, **kwargs):
        super(PneumaticValve, self).__init__(
            parent=parent,
            interlock_suffix=self._interlock_suffix,
            error_suffix=self._error_suffix,
            open_suffix=self._open_state_suffix,
            close_suffix=self._close_state_suffix,
            command_suffix=self._command_suffix,
            **kwargs)

        self.icon = PneumaticValveSymbolIcon(self)
        self.setup_icon()
        self.assemble_layout()
        self.update_status_tooltip()


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
    _interlock_suffix = ":OPN_OK"
    _error_suffix = ":STATE"
    _open_state_suffix = ":OPN_DI"
    _close_state_suffix = ":CLS_DI"
    _command_suffix = ":OPN_SW"

    NAME = "Aperture Valve"

    def __init__(self, parent=None, **kwargs):
        super(ApertureValve, self).__init__(
            parent=parent,
            interlock_suffix=self._interlock_suffix,
            error_suffix=self._error_suffix,
            open_suffix=self._open_state_suffix,
            close_suffix=self._close_state_suffix,
            command_suffix=self._command_suffix,
            **kwargs)

        self.icon = ApertureValveSymbolIcon(self)
        self.setup_icon()
        self.assemble_layout()
        self.update_status_tooltip()


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
    _interlock_suffix = ":VAC_FAULT_OK"
    _error_suffix = ":ERROR"
    _open_state_suffix = ":OPN_DI"
    _close_state_suffix = ":CLS_DI"
    _command_suffix = ":OPN_SW"

    NAME = "Fast Shutter"

    def __init__(self, parent=None, **kwargs):
        super(FastShutter, self).__init__(
            parent=parent,
            interlock_suffix=self._interlock_suffix,
            error_suffix=self._error_suffix,
            open_suffix=self._open_state_suffix,
            close_suffix=self._close_state_suffix,
            command_suffix=self._command_suffix,
            **kwargs)

        self.icon = FastShutterSymbolIcon(self)
        self.setup_icon()
        self.assemble_layout()
        self.update_status_tooltip()


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
    _interlock_suffix = ":ILK_OK"
    _state_suffix = ":STATE"
    _command_suffix = ":OPN_SW"

    NAME = "Needle Valve"

    def __init__(self, parent=None, **kwargs):
        super(NeedleValve, self).__init__(
            parent=parent,
            interlock_suffix=self._interlock_suffix,
            state_suffix=self._state_suffix,
            command_suffix=self._command_suffix,
            **kwargs)

        self.icon = NeedleValveSymbolIcon(self)
        self.setup_icon()
        self.assemble_layout()
        self.update_status_tooltip()


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
    _interlock_suffix = ":ILK_OK"
    _state_suffix = ":STATE"
    _command_suffix = ":OPN_SW"

    NAME = "Proportional Valve"

    def __init__(self, parent=None, **kwargs):
        super(ProportionalValve, self).__init__(
            parent=parent,
            interlock_suffix=self._interlock_suffix,
            state_suffix=self._state_suffix,
            command_suffix=self._command_suffix,
            **kwargs)

        self.icon = ProportionalValveSymbolIcon(self)
        self.setup_icon()
        self.assemble_layout()
        self.update_status_tooltip()


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
        super(RightAngleManualValve, self).__init__(parent=parent, **kwargs)
        self._controls_location = ContentLocation.Hidden
        self.icon = RightAngleManualValveSymbolIcon(self)
        self.setup_icon()
        self.assemble_layout()
        self.update_status_tooltip()

    def sizeHint(self):
        """
        Suggested initial size for the widget.

        Returns
        -------
        size : QSize
        """
        return QSize(64, 64)

    @Property(str, designable=False)
    def channelsPrefix(self):
        pass

    @Property(bool, designable=False)
    def showIcon(self):
        pass

    @Property(ContentLocation, designable=False)
    def controlsLocation(self):
        pass
