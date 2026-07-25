import pytest
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QWidget

from pcdswidgets.common.toolbar.yaml_toolbar import YamlTabLayout


@pytest.mark.parametrize(
    "direction,shape", ((Qt.Horizontal, (6, 2)), (Qt.Vertical, (2, 6))), ids=("Horizontal", "Vertical")
)
def test_yaml_layout_add(qtbot, direction, shape):
    layout = YamlTabLayout(6, direction=direction)
    # Create widgets
    widgets = [QWidget() for i in range(12)]
    for widget in widgets:
        layout.addWidget(widget)
        qtbot.addWidget(widget)

    assert (layout.columnCount(), layout.rowCount()) == shape
