"""
Show a fully functional widget. Useful for development.

Invoke as e.g.
"python -m pcdswidgets.vacuum.demo PneumaticValveDA CRIX:VGC:11"
"""
import sys

import pydm
from pydm.utilities import setup_renderer

from ..gauges import *  # noqa
from ..others import *  # noqa
from ..pumps import *  # noqa
from ..valves import *  # noqa

cls = sys.argv[1]
prefix = sys.argv[2]
setup_renderer()

app = pydm.PyDMApplication(
    ui_file=None,
    hide_nav_bar=True,
    hide_menu_bar=True,
    hide_status_bar=True,
)

widget = globals()[cls]()
widget.channelsPrefix = 'ca://' + sys.argv[2]
app.main_window.set_display_widget(widget)
app.exec()
