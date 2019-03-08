from .base import PCDSSymbolBase
from .mixins import (StateMixin, InterlockMixin, ButtonLabelControl,
                     LabelControl)
from ..icons.gauges import (PiraniGaugeSymbolIcon, HotCathodeGaugeSymbolIcon,
                            ColdCathodeGaugeSymbolIcon)


class PiraniGauge(StateMixin, LabelControl, PCDSSymbolBase):
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

    NAME = "Pirani Gauge"

    def __init__(self, parent=None, **kwargs):
        super(PiraniGauge, self).__init__(
            parent=parent,
            state_suffix=self._state_suffix,
            readback_suffix=self._readback_suffix,
            readback_name='pressure',
            **kwargs)

        self.icon = PiraniGaugeSymbolIcon(self)
        self.setup_icon()
        self.assemble_layout()
        self.update_status_tooltip()


class HotCathodeGauge(InterlockMixin, StateMixin, ButtonLabelControl,
                      PCDSSymbolBase):
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

    NAME = "Hot Cathode Gauge"

    def __init__(self, parent=None, **kwargs):
        super(HotCathodeGauge, self).__init__(
            parent=parent,
            interlock_suffix=self._interlock_suffix,
            state_suffix=self._state_suffix,
            command_suffix=self._command_suffix,
            readback_suffix=self._readback_suffix,
            readback_name='pressure',
            **kwargs)

        self.icon = HotCathodeGaugeSymbolIcon(self)
        self.setup_icon()
        self.assemble_layout()
        self.update_status_tooltip()


class ColdCathodeGauge(InterlockMixin, StateMixin, ButtonLabelControl,
                       PCDSSymbolBase):
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

    NAME = "Cold Cathode Gauge"

    def __init__(self, parent=None, **kwargs):
        super(ColdCathodeGauge, self).__init__(
            parent=parent,
            interlock_suffix=self._interlock_suffix,
            state_suffix=self._state_suffix,
            command_suffix=self._command_suffix,
            readback_suffix=self._readback_suffix,
            readback_name='pressure',
            **kwargs)

        self.icon = ColdCathodeGaugeSymbolIcon(self)
        self.setup_icon()
        self.assemble_layout()
        self.update_status_tooltip()
