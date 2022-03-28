"""
Show a fully functional widget. Useful for development.

Invoke as e.g.
"python -m pcdswidgets.vacuum.demo PneumaticValveDA CRIX:VGC:11"
"""
import sys

from qtpy.QtWidgets import QApplication

from ..gauges import * # noqa
from ..others import * # noqa
from ..pumps import * # noqa
from ..valves import * # noqa


cls = sys.argv[1]
app = QApplication([])
widget = globals()[cls]()
widget.channelsPrefix = 'ca://' + sys.argv[2]
widget.show()
app.exec()
