from dataclasses import dataclass

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
    icon : IconOptions, str, or None, optional
        The icon to use to represent this widget in the qt sidebar.
        If an IconOptions enum, we'll use PyDM's iconfont to pick the matching icon.
        If a str, we'll load the image file from the icons folder that matches this name.
        If None (the default), we'll use the default icon, or we'll look for a user-defined
        get_designer_icon staticmethod that returns a QIcon.
    """

    group: str
    is_container: bool
    icon: IconOptions | str | None = None
