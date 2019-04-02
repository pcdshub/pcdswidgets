import pytest
from qtpy.QtCore import Qt
from qtpy.QtGui import QColor, QBrush

import pcdswidgets.icons
from pcdswidgets.icons.base import BaseSymbolIcon


icons = [getattr(pcdswidgets.icons, icon)
         for icon in pcdswidgets.icons.__all__]


@pytest.mark.parametrize('icon_class', icons, ids=pcdswidgets.icons.__all__)
def test_icon_smoke(qtbot, icon_class):
    icon = icon_class()
    qtbot.addWidget(icon)
    icon.show()


@pytest.fixture(scope='function')
def icon(qtbot):
    icon = BaseSymbolIcon()
    qtbot.addWidget(icon)
    return icon


@pytest.mark.parametrize('prop,value',
                         [('brush', QBrush(QColor(0, 0, 0), Qt.SolidPattern)),
                          ('penStyle', Qt.DotLine),
                          ('penColor', QColor(0, 0, 0)),
                          ('penWidth', 2.0)],
                         ids=('brush', 'penStyle', 'penColor', 'penWidth'))
def test_icon_properties(icon, prop, value):
    setattr(icon, prop, value)
    assert getattr(icon, prop) == value
