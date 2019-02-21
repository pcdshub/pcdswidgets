from qtpy.QtWidgets import QApplication

from pcdswidgets.icons.others import RGASymbolIcon as Icon

app = QApplication([])
tp = Icon()
tp.setFixedSize(64, 64)
tp.show()
app.exec_()
