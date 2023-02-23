from pydm.widgets.display_format import DisplayFormat
from qtpy.QtCore import Property, QSize

from ..icons.pumps import (GetterPumpSymbolIcon, IonPumpSymbolIcon,
                           ScrollPumpSymbolIcon, TurboPumpSymbolIcon)
from .base import ContentLocation, PCDSSymbolBase
from .mixins import (ButtonControl, ButtonLabelControl, ErrorMixin,
                     InterlockMixin, StateMixin)


class IonPump(
    InterlockMixin, ErrorMixin, StateMixin, ButtonLabelControl, PCDSSymbolBase
):
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

        IonPump[interlocked="true"] #interlock {
            border: 5px solid red;
        }
        IonPump[interlocked="false"] #interlock {
            border: 0px;
        }
        IonPump[error="true"] #icon {
            qproperty-penStyle: "Qt::DotLine";
            qproperty-penWidth: 2;
            qproperty-brush: red;
        }
        IonPump[state="On"] #icon {
            qproperty-penColor: green;
            qproperty-penWidth: 2;
        }

    """

    _qt_designer_ = {
        "group": "PCDS Pumps",
        "is_container": False,
    }
    _interlock_suffix = ":ILK_OK_RBV"
    _error_suffix = ":ERROR_RBV"
    _state_suffix = ":STATE_RBV"
    _command_suffix = ":HV_SW"
    _readback_suffix = ":PRESS_RBV"

    NAME = "Ion Pump"
    EXPERT_OPHYD_CLASS = "pcdsdevices.pump.PIPPLC"

    def __init__(self, parent=None, **kwargs):
        super().__init__(
            parent=parent,
            interlock_suffix=self._interlock_suffix,
            error_suffix=self._error_suffix,
            state_suffix=self._state_suffix,
            command_suffix=self._command_suffix,
            readback_suffix=self._readback_suffix,
            readback_name="pressure",
            **kwargs
        )
        self.icon = IonPumpSymbolIcon(parent=self)
        self.readback_label.displayFormat = DisplayFormat.Exponential

    def sizeHint(self):
        return QSize(180, 80)


class TurboPump(InterlockMixin, ErrorMixin, StateMixin, ButtonControl, PCDSSymbolBase):
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

        TurboPump[interlocked="true"] #interlock {
            border: 5px solid red;
        }
        TurboPump[interlocked="false"] #interlock {
            border: 0px;
        }
        TurboPump[error="true"] #icon {
            qproperty-penStyle: "Qt::DotLine";
            qproperty-penWidth: 2;
            qproperty-brush: red;
        }
        TurboPump[state="Accelerating"] #icon {
            qproperty-centerBrush: red;
        }

    """

    _qt_designer_ = {
        "group": "PCDS Pumps",
        "is_container": False,
    }
    _interlock_suffix = ":ILK_OK_RBV"
    _error_suffix = ":FAULT_RBV"
    _state_suffix = ":STATE_RBV"
    _command_suffix = ":RUN_SW"

    NAME = "Turbo Pump"
    EXPERT_OPHYD_CLASS = "pcdsdevices.pump.PTMPLC"

    def __init__(self, parent=None, **kwargs):
        super().__init__(
            parent=parent,
            interlock_suffix=self._interlock_suffix,
            error_suffix=self._error_suffix,
            state_suffix=self._state_suffix,
            command_suffix=self._command_suffix,
            **kwargs)
        self.icon = TurboPumpSymbolIcon(parent=self)

    def sizeHint(self):
        return QSize(180, 80)


class ScrollPump(InterlockMixin, ErrorMixin, StateMixin, ButtonControl, PCDSSymbolBase):
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

        ScrollPump[interlocked="true"] #interlock {
            border: 5px solid red;
        }
        ScrollPump[interlocked="false"] #interlock {
            border: 0px;
        }
        ScrollPump[error="true"] #icon {
            qproperty-penStyle: "Qt::DotLine";
            qproperty-penWidth: 2;
            qproperty-brush: red;
        }
        ScrollPump[state="Accelerating"] #icon {
            qproperty-centerBrush: red;
        }

    """

    _qt_designer_ = {
        "group": "PCDS Pumps",
        "is_container": False,
    }
    _interlock_suffix = ":ILK_OK_RBV"
    _error_suffix = ":ERROR_RBV"
    _state_suffix = ":STATE_RBV"
    _command_suffix = ":RUN_SW"

    NAME = "Scroll Pump"
    EXPERT_OPHYD_CLASS = "pcdsdevices.pump.PROPLC"

    def __init__(self, parent=None, **kwargs):
        super().__init__(
            parent=parent,
            interlock_suffix=self._interlock_suffix,
            error_suffix=self._error_suffix,
            state_suffix=self._state_suffix,
            command_suffix=self._command_suffix,
            **kwargs)
        self.icon = ScrollPumpSymbolIcon(parent=self)

    def sizeHint(self):
        return QSize(180, 80)


class GetterPump(PCDSSymbolBase):
    """
    A Symbol Widget representing a Getter Pump with the proper icon.

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
        "group": "PCDS Pumps",
        "is_container": False,
    }
    NAME = "Getter Pump"

    def __init__(self, parent=None, **kwargs):
        self._controls_location = ContentLocation.Hidden
        super().__init__(parent=parent, **kwargs)
        self.icon = GetterPumpSymbolIcon(parent=self)

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
