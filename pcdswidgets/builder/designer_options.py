from dataclasses import dataclass

from qtpy.QtGui import QIcon

from .icon_options import IconOptions


@dataclass
class DesignerOptions:
    """
    Options for designer.

    Parameters
    ----------
    group : str
        Widgets with the same group will be grouped together in designer.
    is_container : bool
        Set this to True if this widget can contain other widgets (via drag and drop),
        or False otherwise.
    icon : IconOptions, icon, or None
        The icon to use to represent this widget in the qt sidebar.
        If an IconOptions enum, we'll use PyDM's iconfont to pick the matching icon.
        If a QIcon, we'll use it as-is.
        If None, we'll use the default icon.
    """

    group: str
    is_container: bool
    icon: IconOptions | QIcon | None
