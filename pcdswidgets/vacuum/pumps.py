from qtpy.QtCore import QSize, Property

from .base import PCDSSymbolBase, ContentLocation
from .mixins import (InterlockMixin, ErrorMixin, StateMixin, ButtonControl,
                     ButtonLabelControl)
from ..icons.pumps import (IonPumpSymbolIcon, TurboPumpSymbolIcon,
                           ScrollPumpSymbolIcon, GetterPumpSymbolIcon)


class IonPump(InterlockMixin, ErrorMixin, StateMixin, ButtonLabelControl,
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
    _command_suffix = ":HV_SW"
    _readback_suffix = ":PRESS"

    NAME = "Ion Pump"

    def __init__(self, parent=None, **kwargs):
        self.icon = IonPumpSymbolIcon()
        super(IonPump, self).__init__(parent=parent,
                                      interlock_suffix=self._interlock_suffix,
                                      error_suffix=self._error_suffix,
                                      state_suffix=self._state_suffix,
                                      command_suffix=self._command_suffix,
                                      readback_suffix=self._readback_suffix,
                                      readback_name='pressure',
                                      **kwargs)

    def sizeHint(self):
        return QSize(180, 80)


class TurboPump(InterlockMixin, ErrorMixin, StateMixin, ButtonControl,
                PCDSSymbolBase):
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
    _command_suffix = ":RUN_SW"

    NAME = "Turbo Pump"

    def __init__(self, parent=None, **kwargs):
        self.icon = TurboPumpSymbolIcon()
        super(TurboPump, self).__init__(
            parent=parent,
            interlock_suffix=self._interlock_suffix,
            error_suffix=self._error_suffix,
            state_suffix=self._state_suffix,
            command_suffix=self._command_suffix,
            **kwargs)

    def sizeHint(self):
        return QSize(180, 80)


class ScrollPump(InterlockMixin, ErrorMixin, StateMixin, ButtonControl,
                 PCDSSymbolBase):
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
    _command_suffix = ":RUN_SW"

    NAME = "Scroll Pump"

    def __init__(self, parent=None, **kwargs):
        self.icon = ScrollPumpSymbolIcon()
        super(ScrollPump, self).__init__(
            parent=parent,
            interlock_suffix=self._interlock_suffix,
            error_suffix=self._error_suffix,
            state_suffix=self._state_suffix,
            command_suffix=self._command_suffix,
            **kwargs)

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
    NAME = "Getter Pump"

    def __init__(self, parent=None, **kwargs):
        self.icon = GetterPumpSymbolIcon()
        self._controls_location = ContentLocation.Hidden
        super(GetterPump, self).__init__(parent=parent, **kwargs)

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
        return super(GetterPump, self).channelsPrefix

    @Property(bool, designable=False)
    def showIcon(self):
        return super(GetterPump, self).showIcon

    @Property(ContentLocation, designable=False)
    def controlsLocation(self):
        return super(GetterPump, self).controlsLocation
