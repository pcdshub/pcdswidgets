"""Push button that opens a color picker and exposes the selected color."""

from qtpy.QtCore import Property, Signal
from qtpy.QtGui import QColor
from qtpy.QtWidgets import QColorDialog, QPushButton


class ColorButton(QPushButton):
    """
    Button that displays a color swatch and opens QColorDialog on click.

    Emits a `colorChanged` signal when a new color is selected.
    """

    colorChanged = Signal(QColor)

    def __init__(self, parent=None):
        """Initialize the button with a red default color."""
        super().__init__(parent)

        self._color = QColor("red")
        self._update_button_style()
        self.setMinimumWidth(40)
        self.clicked.connect(self.on_click)

    def get_color(self):
        """Return the currently selected color."""
        return self._color

    def set_color(self, color):
        """Set the button's color and emit the colorChanged signal."""
        color = QColor(color)

        if color != self._color:
            self._color = color
            self._update_button_style()
            self.colorChanged.emit(self._color)

    color = Property(QColor, fget=get_color, fset=set_color)

    def on_click(self):
        """Open the QColorDialog when the button is clicked."""
        new_color = QColorDialog.getColor(self._color, self, "Choose a color")
        if new_color.isValid():
            self.set_color(new_color)

    def _update_button_style(self):
        """Update the button's stylesheet to reflect the current color."""
        # Use a stylesheet for a solid background color
        self.setStyleSheet(f"ColorButton {{background-color: {self._color.name()}; border: 1px solid black;}}")
