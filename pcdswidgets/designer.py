from pydm.widgets.qtplugin_base import qtplugin_factory

from .vacuum.gauges import RoughGauge, HotCathodeGauge, ColdCathodeGauge
from .vacuum.others import RGA
from .vacuum.pumps import IonPump, TurboPump, ScrollPump, GetterPump
from .vacuum.valves import (PneumaticValve, FastShutter, NeedleValve,
                            ProportionalValve, RightAngleManualValve,
                            ApertureValve, ControlValve, ControlOnlyValveNC,
                            ControlOnlyValveNO, PneumaticValveNO)

from .vacuum.base import PCDSSymbolBase

BasePlugin = qtplugin_factory(PCDSSymbolBase, group="PCDS Symbols")

# Valves
PCDSPneumaticValvePlugin = qtplugin_factory(PneumaticValve,
                                            group="PCDS Valves")
PCDSPneumaticValveNOPlugin = qtplugin_factory(PneumaticValveNO,
                                              group="PCDS Valves")
PCDSApertureValvePlugin = qtplugin_factory(ApertureValve, group='PCDS Valves')
PCDSFastShutterPlugin = qtplugin_factory(FastShutter, group="PCDS Valves")

PCDSNeedleValvePlugin = qtplugin_factory(NeedleValve, group="PCDS Valves")
PCDSProportionalValvePlugin = qtplugin_factory(ProportionalValve,
                                               group="PCDS Valves")

PCDSRightAngleManualValve = qtplugin_factory(RightAngleManualValve,
                                             group="PCDS Valves")
PCDSControlValve = qtplugin_factory(ControlValve,
                                    group="PCDS Valves")
PCDSControlOnlyValveNC = qtplugin_factory(ControlOnlyValveNC,
                                          group="PCDS Valves")
PCDSControlOnlyValveNO = qtplugin_factory(ControlOnlyValveNO,
                                          group="PCDS Valves")

# Pumps
PCDSIonPumpPlugin = qtplugin_factory(IonPump, group="PCDS Pumps")
PCDSTurboPumpPlugin = qtplugin_factory(TurboPump, group="PCDS Pumps")
PCDSScrollPumpPlugin = qtplugin_factory(ScrollPump, group="PCDS Pumps")
PCDSGetterPumpPlugin = qtplugin_factory(GetterPump, group="PCDS Pumps")


# Gauges
PCDSRoughGaugePlugin = qtplugin_factory(RoughGauge, group="PCDS Gauges")
PCDSHotCathodeGaugePlugin = qtplugin_factory(HotCathodeGauge,
                                             group="PCDS Gauges")
PCDSColdCathodeGaugePlugin = qtplugin_factory(ColdCathodeGauge,
                                              group="PCDS Gauges")

# Others
PCDSRGAPlugin = qtplugin_factory(RGA, group="PCDS Others")
