"""
Show an icon. Useful for development.

Invoke as e.g. "python -m pcdswidgets.icons.demo ControlValve"
"""
import sys

from qtpy.QtWidgets import QApplication

from .. import *  # noqa

cls = sys.argv[1] + 'SymbolIcon'
app = QApplication([])
icon = globals()[cls]()
icon.show()
app.exec()
