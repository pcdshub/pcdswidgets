from pydm.widgets.display_format import DisplayFormat
from qtpy.QtCore import QSize

from ..icons.gauges import (ColdCathodeGaugeSymbolIcon,
                            HotCathodeGaugeSymbolIcon, RoughGaugeSymbolIcon)
from .base import PCDSSymbolBase
from .mixins import (ButtonLabelControl, InterlockMixin, LabelControl,
                     StateMixin)


class RoughGauge(StateMixin, LabelControl, PCDSSymbolBase):
    """
    A Symbol Widget representing a Rough Gauge with the proper icon and
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

        RoughGauge[state="Off"] {
            qproperty-brush: red;
            color: gray;
        }
        RoughGauge[state="On"] {
            qproperty-brush: green;
            color: black;
        }

    """

    _qt_designer_ = {
        "group": "PCDS Gauges",
        "is_container": False,
    }
    _state_suffix = ":STATE_RBV"
    _readback_suffix = ":PRESS_RBV"

    NAME = "Rough Gauge"
    EXPERT_OPHYD_CLASS = "pcdsdevices.gauge.GaugePLC"

    def __init__(self, parent=None, **kwargs):
        super().__init__(
            parent=parent,
            state_suffix=self._state_suffix,
            readback_suffix=self._readback_suffix,
            readback_name='pressure',
            **kwargs)
        self.icon = RoughGaugeSymbolIcon(parent=self)
        self.readback_label.displayFormat = DisplayFormat.Exponential

    def sizeHint(self):
        return QSize(70, 60)


class HotCathodeGauge(ButtonLabelControl, InterlockMixin, StateMixin, PCDSSymbolBase):
    """
    A Symbol Widget representing a Hot Cathode Gauge with the proper icon
    and controls.

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

        HotCathodeGauge[interlocked="true"] #interlock {
            border: 5px solid red;
        }
        HotCathodeGauge[interlocked="false"] #interlock {
            border: 0px;
        }
        HotCathodeGauge[state="Error"] #icon {
            qproperty-penColor: red;
            qproperty-penWidth: 2;
        }

    """

    _qt_designer_ = {
        "group": "PCDS Gauges",
        "is_container": False,
    }
    _interlock_suffix = ":ILK_OK_RBV"
    _state_suffix = ":STATE_RBV"
    _readback_suffix = ":PRESS_RBV"
    _command_suffix = ":HV_SW"

    NAME = "Hot Cathode Gauge"

    def __init__(self, parent=None, **kwargs):
        super().__init__(
            parent=parent,
            interlock_suffix=self._interlock_suffix,
            state_suffix=self._state_suffix,
            command_suffix=self._command_suffix,
            readback_suffix=self._readback_suffix,
            readback_name='pressure',
            **kwargs)
        self.icon = HotCathodeGaugeSymbolIcon(parent=self)
        self.readback_label.displayFormat = DisplayFormat.Exponential

    def sizeHint(self):
        return QSize(180, 80)


class ColdCathodeGauge(InterlockMixin, StateMixin, ButtonLabelControl, PCDSSymbolBase):
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

        ColdCathodeGauge[interlocked="true"] #interlock {
            border: 5px solid red;
        }
        ColdCathodeGauge[interlocked="false"] #interlock {
            border: 0px;
        }
        ColdCathodeGauge[state="Error"] #icon {
            qproperty-penColor: red;
            qproperty-penWidth: 2;
        }

    """

    _qt_designer_ = {
        "group": "PCDS Gauges",
        "is_container": False,
    }
    _interlock_suffix = ":ILK_OK_RBV"
    _state_suffix = ":STATE_RBV"
    _readback_suffix = ":PRESS_RBV"
    _command_suffix = ":HV_SW"

    NAME = "Cold Cathode Gauge"
    EXPERT_OPHYD_CLASS = "pcdsdevices.gauge.GCCPLC"

    def __init__(self, parent=None, **kwargs):
        super().__init__(
            parent=parent,
            interlock_suffix=self._interlock_suffix,
            state_suffix=self._state_suffix,
            command_suffix=self._command_suffix,
            readback_suffix=self._readback_suffix,
            readback_name='pressure',
            **kwargs)
        self.icon = ColdCathodeGaugeSymbolIcon(parent=self)
        self.readback_label.displayFormat = DisplayFormat.Exponential

    def sizeHint(self):
        return QSize(180, 80)
