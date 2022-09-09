from unittest.mock import Mock

import pytest
from qtpy.QtCore import Qt
from qtpy.QtGui import QBrush, QColor

import pcdswidgets.icons
from pcdswidgets.icons.base import BaseSymbolIcon

icons = [getattr(pcdswidgets.icons, icon)
         for icon in pcdswidgets.icons.__all__]


@pytest.mark.parametrize('icon_class', icons, ids=pcdswidgets.icons.__all__)
def test_icon_smoke(qtbot, icon_class):
    icon = icon_class()
    qtbot.addWidget(icon)
    with qtbot.waitExposed(icon):
        icon.show()
    icon.repaint()


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


def test_icon_clicks(qtbot, icon):
    mock = Mock()
    icon.clicked.connect(mock)
    qtbot.mouseClick(icon, Qt.LeftButton)
    assert mock.called
