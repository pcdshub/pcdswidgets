"""Registry of savable widget properties for ViewSaver."""

import logging
from typing import Callable

from qtpy.QtWidgets import QWidget

logger = logging.getLogger(__name__)


def _to_bool(value: object) -> bool:
    """Coerce a QSettings value (often the string ``"true"``/``"false"``) to bool."""
    if isinstance(value, str):
        return value.strip().lower() in ("true", "1", "yes", "on")
    return bool(value)


# dict of properties that should have persistance given a ClassName
#
# Format is:
# Qt class name -> { propKey: (getter_method_name, setter_method_name, converter) }
#
# ``converter`` is a callable applied to the raw value read from QSettings
# (which is stored as a string in IniFormat) to coerce it back to the type the
# setter expects.  Use ``lambda v: v`` when no conversion is required.

WIDGET_REGISTRY: dict[str, dict[str, tuple[str, str, Callable]]] = {
    # QT BASE
    "QTabWidget": {"currentIndex": ("currentIndex", "setCurrentIndex", int)},
    "QComboBox": {"currentIndex": ("currentIndex", "setCurrentIndex", int)},
    "QGroupBox": {"checked": ("isChecked", "setChecked", _to_bool)},
    "QCheckBox": {"checked": ("isChecked", "setChecked", _to_bool)},
    "QSplitter": {"state": ("saveState", "restoreState", lambda v: v)},
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
) -> dict[str, tuple[Callable, Callable, Callable]] | None:
    """Resolve bound getter/setter callables for each persisted property.

    Returns a mapping ``{propKey: (getter, setter, converter)}`` for
    *widget_name*, or ``None`` if the widget cannot be found or has no
    registered properties.
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
    for prop_name, (getter, setter, converter) in props.items():
        resolved_props[prop_name] = (
            getattr(widget, getter, None),
            getattr(widget, setter, None),
            converter,
        )
    return resolved_props
