import pytest

import pcdswidgets.icons

icons = [getattr(pcdswidgets.icons, icon)
         for icon in pcdswidgets.icons.__all__]


@pytest.mark.parametrize('icon_class', icons, ids=pcdswidgets.icons.__all__)
def test_icon_smoke(qtbot, icon_class):
    icon = icon_class()
    qtbot.addWidget(icon)
    icon.show()
