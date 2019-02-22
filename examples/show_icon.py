import os
from qtpy.QtWidgets import QApplication, QWidget

import pcdswidgets.icons as icons


def screenshot(widget, filename):
    """
    Takes a screenshot of the widget window, saves png image to file
    """
    s = str(filename) + ".png"
    print("Filename: ", s)
    p = QWidget.grab(widget)
    p.save(s, 'png')

app = QApplication([])

for ic in icons.__all__:
    tp = ic()
    tp.setFixedSize(64, 64)
    tp.show()
    path = os.path.join(os.path.dirname(__file__), "icons",
                        tp.__class__.__name__)
    screenshot(tp, path)
