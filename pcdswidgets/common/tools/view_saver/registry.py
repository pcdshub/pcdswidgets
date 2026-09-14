"""Registry of savable widget properties for ViewSaver."""

import logging
from typing import Callable

from qtpy.QtWidgets import QWidget

logger = logging.getLogger(__name__)

# dict of properties that should have persistance given a ClassName
#
# Format is:
# Qt class name -> { propKey: (getter_method_name, setter_method_name) }
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

def discover_widgets(root: QWidget) -> list[str]:
    """Return sorted objectNames of *root*'s children ViewSaver can persist.

    Widgets without an objectName or without any registered properties are
    skipped.
    """
    names: list[str] = []
    for w in root.findChildren(QWidget):
        name = w.objectName()
        if not name:
            continue
        class_name = type(w).__name__
        if class_name in WIDGET_REGISTRY:
            names.append(name)
    return sorted(names)


def resolve_widget(
    root: QWidget, widget_name: str
) -> dict[str, tuple[Callable, Callable]] | None:
    """Resolve bound getter/setter callables for each persisted property.

    Returns a mapping ``{propKey: (getter, setter)}`` for *widget_name*, or
    ``None`` if the widget cannot be found or has no registered properties.
    """
    widget = root.findChild(QWidget, widget_name)
    if widget is None:
        logger.error(f"Failed to resolve widget {widget_name}")
        return None
    resolved_props = {}
    class_name = type(widget).__name__
    props = WIDGET_REGISTRY.get(class_name)
    if props is None:
        logger.error(f"No registered properties for {class_name}")
        return None
    for prop_name, (getter, setter ) in props.items():
        resolved_props[prop_name] = getattr(widget, getter, None), getattr(widget, setter, None)
    return resolved_props
