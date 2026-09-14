"""Registry of savable widget properties for ViewSaver."""

import logging
from typing import Any

from qtpy.QtWidgets import QWidget

logger = logging.getLogger(__name__)

# dict of properties that should have persistance given a ClassName
#
# Format is:
# Qt type name -> [{ propKey: (getter_method_name, setter_method_name) }]
#

WIDGET_REGISTRY: dict[str, dict[str, tuple[str, str]]] = {
    # QT BASE
    "QTabWidget": {"currentIndex": ("currentIndex", "setCurrentIndex")},
    "QComboBox": {"currentIndex": ("currentIndex", "setCurrentIndex")},
    "QGroupBox": {"checked": ("isChecked", "setChecked")},
    "QCheckBox": {"checked": ("isChecked", "setChecked")},
    "QSplitter": {"state": ("saveState", "restoreState")},
    # Imaging
    # Motion

}

def resolve_widget(window, widget_name):
    """Resolves all the "persisted" attribute names for a given widget name.
    """
    resolved = {}
    widget = getattr(window, widget_name, None)
    if widget is None:
        logger.error(f"Failed to resolve widget {widget_name}")
        return None
    class_name = str(type(widget))
    props = WIDGET_REGISTRY[class_name]
    for prop_name, (getter, setter ) in props.items():
        resolved[prop_name] = getattr(widget, getter, None), getattr(widget, setter, None)
    return resolved
