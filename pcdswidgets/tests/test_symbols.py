"""Tests for the vector-drawn symbol icon classes."""

from unittest.mock import Mock

import pytest
from qtpy.QtCore import Qt
from qtpy.QtGui import QBrush, QColor

import pcdswidgets.symbols
from pcdswidgets.symbols.base import BaseSymbolIcon

icons = [getattr(pcdswidgets.symbols, icon) for icon in pcdswidgets.symbols.__all__]


@pytest.mark.parametrize("icon_class", icons, ids=pcdswidgets.symbols.__all__)
def test_icon_smoke(qtbot, icon_class):
    """Test icon smoke."""
    icon = icon_class()
    qtbot.addWidget(icon)
    with qtbot.waitExposed(icon):
        icon.show()
    icon.repaint()


@pytest.fixture(scope="function")
def icon(qtbot):
    """Provide a fresh BaseSymbolIcon for the test."""
    icon = BaseSymbolIcon()
    qtbot.addWidget(icon)
    return icon


@pytest.mark.parametrize(
    "prop,value",
    [
        ("brush", QBrush(QColor(0, 0, 0), Qt.SolidPattern)),
        ("penStyle", Qt.DotLine),
        ("penColor", QColor(0, 0, 0)),
        ("penWidth", 2.0),
    ],
    ids=("brush", "penStyle", "penColor", "penWidth"),
)
def test_icon_properties(icon, prop, value):
    """Test icon properties."""
    setattr(icon, prop, value)
    assert getattr(icon, prop) == value


def test_icon_clicks(qtbot, icon):
    """Test icon clicks."""
    mock = Mock()
    icon.clicked.connect(mock)
    qtbot.mouseClick(icon, Qt.LeftButton)
    assert mock.called
