from setuptools import find_packages, setup

import versioneer

with open('requirements.txt') as f:
    requirements = f.read().split()

git_requirements = [r for r in requirements if r.startswith('git+')]
requirements = [r for r in requirements if not r.startswith('git+')]

if len(git_requirements) > 0:
    print("User must install \n" +
          "\n".join(f' {r}' for r in git_requirements) +
          "\n\nmanually")

# Widgets to be displayed in the Qt Designer:
designer_widgets = [
    "SymbolBase=pcdswidgets.vacuum.base:PCDSSymbolBase",
    "FilterSortWidgetTable=pcdswidgets.table:FilterSortWidgetTable",
    "PneumaticValve=pcdswidgets.vacuum.valves:PneumaticValve",
    "PneumaticValveNO=pcdswidgets.vacuum.valves:PneumaticValveNO",
    "PneumaticValveDA=pcdswidgets.vacuum.valves:PneumaticValveDA",
    "ApertureValve=pcdswidgets.vacuum.valves:ApertureValve",
    "FastShutter=pcdswidgets.vacuum.valves:FastShutter",
    "NeedleValve=pcdswidgets.vacuum.valves:NeedleValve",
    "ProportionalValve=pcdswidgets.vacuum.valves:ProportionalValve",
    "RightAngleManualValve=pcdswidgets.vacuum.valves:RightAngleManualValve",
    "ControlValve=pcdswidgets.vacuum.valves:ControlValve",
    "ControlOnlyValveNC=pcdswidgets.vacuum.valves:ControlOnlyValveNC",
    "ControlOnlyValveNO=pcdswidgets.vacuum.valves:ControlOnlyValveNO",

    "IonPump=pcdswidgets.vacuum.pumps:IonPump",
    "TurboPump=pcdswidgets.vacuum.pumps:TurboPump",
    "ScrollPump=pcdswidgets.vacuum.pumps:ScrollPump",
    "GetterPump=pcdswidgets.vacuum.pumps:GetterPump",

    "RoughGauge=pcdswidgets.vacuum.gauges:RoughGauge",
    "HotCathodeGauge=pcdswidgets.vacuum.gauges:HotCathodeGauge",
    "ColdCathodeGauge=pcdswidgets.vacuum.gauges:ColdCathodeGauge",
    "RGA=pcdswidgets.vacuum.others:RGA",
]

setup(
    name="pcdswidgets",
    author="SLAC National Accelerator Laboratory",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    description="LCLS PyDM Widget Library",
    entry_points={
        "pydm.widget": designer_widgets,
    }
)
