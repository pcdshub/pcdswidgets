from pydm.widgets.qtplugin_base import qtplugin_factory

from .symbols.gauges import PiraniGauge, HotCathodeGauge, ColdCathodeGauge
from .symbols.pumps import IonPump, TurboPump, ScrollPump
from .symbols.valves import PneumaticValve, FastShutter

# Valves
PCDSPneumaticValvePlugin = qtplugin_factory(PneumaticValve,
                                            group="PCDS Valves")
PCDSFastShutterPlugin = qtplugin_factory(FastShutter, group="PCDS Valves")

# Pumps
PCDSIonPumpPlugin = qtplugin_factory(IonPump, group="PCDS Pumps")
PCDSTurboPumpPlugin = qtplugin_factory(TurboPump, group="PCDS Pumps")
PCDSScrollPumpPlugin = qtplugin_factory(ScrollPump, group="PCDS Pumps")

# Gauges
PCDSPiraniGaugePlugin = qtplugin_factory(PiraniGauge, group="PCDS Gauges")
PCDSHotCathodeGaugePlugin = qtplugin_factory(HotCathodeGauge,
                                             group="PCDS Gauges")
PCDSColdCathodeGaugePlugin = qtplugin_factory(ColdCathodeGauge,
                                              group="PCDS Gauges")
