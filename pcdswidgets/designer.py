from pydm.widgets.qtplugin_base import qtplugin_factory

from .symbols.gauges import PiraniGauge, HotCathodeGauge, ColdCathodeGauge
from .symbols.others import RGA
from .symbols.pumps import IonPump, TurboPump, ScrollPump, GetterPump
from .symbols.valves import (PneumaticValve, FastShutter, NeedleValve,
                             ProportionalValve, RightAngleManualValve)

# Valves
PCDSPneumaticValvePlugin = qtplugin_factory(PneumaticValve,
                                            group="PCDS Valves")
PCDSFastShutterPlugin = qtplugin_factory(FastShutter, group="PCDS Valves")

PCDSNeedleValvePlugin = qtplugin_factory(NeedleValve, group="PCDS Valves")
PCDSProportionalValvePlugin = qtplugin_factory(ProportionalValve,
                                               group="PCDS Valves")

PCDSRightAngleManualValve = qtplugin_factory(RightAngleManualValve,
                                             group="PCDS Valves")

# Pumps
PCDSIonPumpPlugin = qtplugin_factory(IonPump, group="PCDS Pumps")
PCDSTurboPumpPlugin = qtplugin_factory(TurboPump, group="PCDS Pumps")
PCDSScrollPumpPlugin = qtplugin_factory(ScrollPump, group="PCDS Pumps")
PCDSGetterPumpPlugin = qtplugin_factory(GetterPump, group="PCDS Pumps")


# Gauges
PCDSPiraniGaugePlugin = qtplugin_factory(PiraniGauge, group="PCDS Gauges")
PCDSHotCathodeGaugePlugin = qtplugin_factory(HotCathodeGauge,
                                             group="PCDS Gauges")
PCDSColdCathodeGaugePlugin = qtplugin_factory(ColdCathodeGauge,
                                              group="PCDS Gauges")

# Others
PCDSRGAPlugin = qtplugin_factory(RGA, group="PCDS Others")
