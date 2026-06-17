import logging
import os

from pydm.widgets.display_format import DisplayFormat
from qtpy.QtCore import Property, QSize

from ..symbols.pumps import GetterPumpSymbolIcon, IonPumpSymbolIcon, ScrollPumpSymbolIcon, TurboPumpSymbolIcon
from .base import ContentLocation, PCDSSymbolBase
from .mixins import ButtonControl, ButtonLabelControl, ErrorMixin, InterlockMixin, StateMixin

logger = logging.getLogger(__name__)


class IonPump(InterlockMixin, ErrorMixin, StateMixin, ButtonLabelControl, PCDSSymbolBase):
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
        "group": "ECS Vacuum Pumps",
        "is_container": False,
    }
    _interlock_suffix = ":ILK_OK_RBV"
    _error_suffix = ":ERROR_RBV"
    _state_suffix = ":STATE_RBV"
    _command_suffix = ":HV_SW"
    _readback_suffix = ":PRESS_RBV"

    NAME = "Ion Pump"
    EXPERT_OPHYD_CLASS = "pcdsdevices.pump.PIPPLC"

    # Per-ophyd-class suffix overrides. Any suffix not listed for a given
    # ophyd class falls back to the class-level default above. These are
    # applied whenever the expertOphydClass property changes (including when
    # the Designer applies the saved property after construction), and the
    # channels are rebuilt so the new suffixes take effect.
    SUFFIX_MAP = {
        "pcdsdevices.pump.PIPCombined": {
            "interlock_suffix": False,
            "error_suffix": ":ERROR",
            "state_suffix": ":STATUS",
            "command_suffix": ":STATEDES",
            "readback_suffix": ":PRESS_RBV",
        },
    }

    def __init__(self, parent=None, **kwargs):
        super().__init__(
            parent=parent,
            interlock_suffix=self._interlock_suffix,
            error_suffix=self._error_suffix,
            state_suffix=self._state_suffix,
            command_suffix=self._command_suffix,
            readback_suffix=self._readback_suffix,
            readback_name="pressure",
            **kwargs,
        )
        self.icon = IonPumpSymbolIcon(parent=self)
        self.readback_label.displayFormat = DisplayFormat.Exponential

    @PCDSSymbolBase.expertOphydClass.setter
    def expertOphydClass(self, klass):
        """
        Set the expert ophyd class and apply any suffix overrides mapped to it.

        When the ophyd class changes, the per-class suffixes (if any) are
        applied and the channels are rebuilt so they point at the correct PVs.
        """
        if self.expertOphydClass == klass:
            return
        self._expert_ophyd_class = klass

        overrides = self.SUFFIX_MAP.get(klass, {})
        self._interlock_suffix = overrides.get("interlock_suffix", type(self)._interlock_suffix)
        self._error_suffix = overrides.get("error_suffix", type(self)._error_suffix)
        self._state_suffix = overrides.get("state_suffix", type(self)._state_suffix)
        self._command_suffix = overrides.get("command_suffix", type(self)._command_suffix)
        self._readback_suffix = overrides.get("readback_suffix", type(self)._readback_suffix)

        # Rebuild channels so the new suffixes take effect (only meaningful
        # once a channel prefix has been provided).
        if self._channels_prefix:
            self.destroy_channels()
            self.create_channels()

    def sizeHint(self):
        return QSize(180, 80)

    def get_expert_ui_paths(self, expert_key):
        """
        Provide paths to expert UIs for IonPump.

        Parameters
        ----------
        expert_key : str
            The expertOphydClass value.

        Returns
        -------
        list[str]
            Paths to matching .ui files, or an empty list.
        """
        if not expert_key:
            return []
        folder = expert_key.rsplit(".", 1)[-1]

        ui_dir = os.path.join(os.path.dirname(__file__), "..", "ui", "vacuum", "pump_screens", folder)
        if not os.path.isdir(ui_dir):
            return []

        # Define preferred tab order
        preferred_order = ["detailed.ui", "expert.ui", "controller.ui"]
        all_files = [f for f in os.listdir(ui_dir) if f.endswith(".ui")]

        # Sort by preferred_order, then append any extras not in the list
        ordered_files = [f for f in preferred_order if f in all_files] + [f for f in all_files if f not in preferred_order]

        ui_paths = [os.path.join(ui_dir, filename) for filename in ordered_files]
        return ui_paths

    def get_expert_macros(self, expert_key: str, prefix: str) -> dict[str, str]:
        """
        Provide expert-screen macros for IonPump.

        Subclasses can tailor this further for IOC naming differences.
        """
        macros = super().get_expert_macros(expert_key, prefix)

        controller_base = ""
        controller_pv = f"{prefix}:VPCNAME"

        try:
            from epics import caget
        except ImportError:
            logger.debug("pyepics is unavailable; leaving controller_base empty for %s", controller_pv)
        else:
            try:
                controller_value = caget(controller_pv, timeout=1.0)
            except Exception:
                logger.warning("Unable to resolve %s for IonPump expert macros", controller_pv, exc_info=True)
            else:
                if controller_value is None:
                    logger.debug("No controller base returned from %s", controller_pv)
                else:
                    controller_base = str(controller_value).strip()
                    logger.debug("Resolved controller_base '%s' from %s for IonPump expert macros", controller_base, controller_pv)

        # Leave the macro empty if no controller can be resolved so the
        # expert screen still opens, but its controller PVs will not connect.
        macros["controller"] = controller_base
        return macros



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
        "group": "ECS Vacuum Pumps",
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
            **kwargs,
        )
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
        "group": "ECS Vacuum Pumps",
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
            **kwargs,
        )
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
        "group": "ECS Vacuum Pumps",
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
