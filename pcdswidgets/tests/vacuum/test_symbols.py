import pytest

import pcdswidgets.vacuum

symbols = [getattr(pcdswidgets.vacuum, symbol)
           for symbol in pcdswidgets.vacuum.__all__]


@pytest.mark.parametrize('symbol', symbols, ids=pcdswidgets.vacuum.__all__)
def test_vacuum_widgets(qtbot, symbol):
    widget = symbol()
    qtbot.addWidget(widget)
    widget.create_channels()
    widget.destroy_channels()
