from qtpy.QtWidgets import QPushButton, QColorDialog
from qtpy.QtGui import QColor, QPalette
from qtpy.QtCore import Signal
from qtpy.QtCore import Property

class ColorButton(QPushButton):
    """
    A button that displays a color swatch. When clicked, it opens
    QColorDialog to let the user choose a new color.

    Emits a `colorChanged` signal when a new color is selected.
    """

    colorChanged = Signal(QColor)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._color = None
        self.setMinimumWidth(40)
        self.clicked.connect(self.on_click)

        self.set_color(QColor("red"))

    def get_color(self):
        return self._color

    def set_color(self, color):
        """Sets the button's color and emits the colorChanged signal."""
        color = QColor(color)

        if color != self._color:
            self._color = color
            self._update_button_style()
            self.colorChanged.emit(self._color)

    color = Property(QColor, fget=get_color, fset=set_color)

    def on_click(self):
        """Opens the QColorDialog when the button is clicked."""
        new_color = QColorDialog.getColor(self._color, self, "Choose a color")
        if new_color.isValid():
            self.set_color(new_color)

    def _update_button_style(self):
        """Updates the button's stylesheet to reflect the current color."""
        # Use a stylesheet for a solid background color
        self.setStyleSheet(f"ColorButton {{background-color: {self._color.name()}; border: 1px solid black;}}")
