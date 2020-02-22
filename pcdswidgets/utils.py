import sys
import inspect
import importlib
import logging
from qtpy.QtWidgets import QWidget

logger = logging.getLogger(__name__)


def refresh_style(widget):
    """
    Method that traverse the widget tree starting at `widget` and refresh the
    style for this widget and its childs.

    Parameters
    ----------
    widget : QWidget
    """
    widgets = [widget]
    widgets.extend(widget.findChildren(QWidget))
    for child_widget in widgets:
        child_widget.style().unpolish(child_widget)
        child_widget.style().polish(child_widget)
        child_widget.update()
        if child_widget != widget:
            refresh_style(child_widget)


def find_ancestor_for_widget(widget, klass):
    w = widget
    while w.parent() is not None:
        w = w.parent()
        if isinstance(w, klass):
            return w
    return None


def _import_helper(klass):
    """
    Interpret a device class import string and extract the class object.

    Parameters
    ----------
    klass : str
        The module path to find the class e.g.
        ``"pcdsdevices.device_types.IPM"``

    Returns
    -------
    cls : type
        The class referred to by the input string.
    """
    mod, cls = klass.rsplit('.', 1)
    # Import the module if not already present
    # Otherwise use the stashed version in sys.modules
    if mod in sys.modules:
        logger.debug("Using previously imported version of %s", mod)
        mod = sys.modules[mod]
    else:
        logger.debug("Importing %s", mod)
        mod = importlib.import_module(mod)
    # Gather our device class from the given module
    try:
        return getattr(mod, cls)
    except AttributeError as exc:
        raise ImportError("Unable to import %s from %s" %
                          (cls, mod.__name__)) from exc


def get_typhos_display(*, klass, name="", prefix):
    try:
        import typhos
    except ImportError:
        logger.exception('Typhos is unavailable. '
                         'Please install it to use this feature')
        return None

    if inspect.isclass(klass):
        k = klass
    else:
        k = _import_helper(klass)

    if not k:
        logger.error(f'Failed to import class {klass}')
        return None

    try:
        obj = k(name=name, prefix=prefix)
    except Exception:
        logger.exception('Failed to instantiate object for class %s '
                         'using prefix %s', klass, prefix)

    try:
        display = typhos.TyphosDeviceDisplay.from_device(obj)
        return display
    except Exception:
        logger.exception('Failed to generate TyphosDeviceDisplay from '
                         'device %s', obj)
        return None
