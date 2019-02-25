from qtpy.QtCore import QSize, Property
from qtpy.QtWidgets import QSizePolicy

from .base import PCDSSymbolBase, ContentLocation
from ..icons.others import RGASymbolIcon


class RGA(PCDSSymbolBase):
    """
    A Symbol Widget representing a Residual Gas Analyzer with the proper icon.

    Parameters
    ----------
    parent : QWidget
        The parent widget for the symbol

    Notes
    -----
    This widget allow for high customization through the Qt Stylesheets
    mechanism.
    As this widget is composed by internal widgets, their names can be used as
    selectors when writing your stylesheet to be used with this widget.
    Properties are also available to offer wider customization possibilities.

    **Internal Components**

    +-----------+--------------+---------------------------------------+
    |Widget Name|Type          |What is it?                            |
    +===========+==============+=======================================+
    |interlock  |QFrame        |The QFrame wrapping this whole widget. |
    +-----------+--------------+---------------------------------------+
    |controls   |QFrame        |The QFrame wrapping the controls panel.|
    +-----------+--------------+---------------------------------------+
    |icon       |BaseSymbolIcon|The widget containing the icon drawing.|
    +-----------+--------------+---------------------------------------+

    """
    NAME = "Residual Gas Analyzer"

    def __init__(self, parent=None, **kwargs):
        super(RGA, self).__init__(
            parent=parent,
            **kwargs)
        self._controls_location = ContentLocation.Hidden
        self.icon = RGASymbolIcon(self)
        self.icon.setMinimumSize(16, 16)
        self.icon.setSizePolicy(QSizePolicy.Expanding,
                                QSizePolicy.Expanding)
        self.icon.setVisible(self._show_icon)
        self.iconSize = 32

        self.assemble_layout()
        self.update_status_tooltip()

    def sizeHint(self):
        """
        Suggested initial size for the widget.

        Returns
        -------
        size : QSize
        """
        return QSize(64, 64)

    @Property(str, designable=False)
    def channelsPrefix(self):
        pass

    @Property(bool, designable=False)
    def showIcon(self):
        pass