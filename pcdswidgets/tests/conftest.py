############
# Standard #
############
import logging

import pytest
from pytestqt.qtbot import QtBot

from pcdswidgets.common.dock.tab_dock import TabDock

logger = logging.getLogger(__name__)


@pytest.fixture(scope="function")
def tab_dock(qtbot: QtBot) -> TabDock:
    dock = TabDock()
    dock.show()
    qtbot.addWidget(dock)
    return dock
