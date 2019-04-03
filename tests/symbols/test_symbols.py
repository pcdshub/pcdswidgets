import pytest

import pcdswidgets.symbols


symbols = [getattr(pcdswidgets.symbols, symbol)
           for symbol in pcdswidgets.symbols.__all__]


@pytest.mark.parametrize('symbol', symbols, ids=pcdswidgets.symbols.__all__)
def test_symbols(qtbot, symbol):
    widget = symbol()
    qtbot.addWidget(widget)
    widget.create_channels()
    widget.destroy_channels()
