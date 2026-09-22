"""Fallback registry of savable widget properties for ViewSaver.

This registry is the exception path used for widget classes
we do not plan to override/subclasswith a ``get_view_saver_properties`` method.
- i.e. built-in Qt widgets and third-party widgets
"""

import json
import logging
from operator import attrgetter
from typing import Callable

from qtpy.QtWidgets import QWidget

logger = logging.getLogger(__name__)


def _identity(value: object) -> object:
    """No-op converter, for values QSettings already round-trips faithfully."""
    return value


def _to_bool(value: object) -> bool:
    """Coerce a QSettings value (often the string ``"true"``/``"false"``) to bool."""
    if isinstance(value, str):
        return value.strip().lower() in ("true", "1", "yes", "on")
    return bool(value)


def _json_default(obj: object) -> object:
    """Fallback encoder for values ``json.dumps`` can't handle natively.

    ``ViewBox.getState()`` embeds numpy arrays; convert to lists.
    """
    if hasattr(obj, "tolist"):
        return obj.tolist()
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")


def _json_dumps(value: object) -> str:
    """``json.dumps`` that tolerates numpy arrays/scalars via ``_json_default``."""
    return json.dumps(value, default=_json_default)


def _make_getter(widget: object, path: str, save_fn: Callable) -> Callable:
    """wrap the widget property getter to return the encoded value.

    ``save_fn`` turns value to what QSettings stores (usually string)
    """
    method = attrgetter(path)(widget)
    return lambda: save_fn(method())


def _make_setter(widget: object, path: str, load_fn: Callable) -> Callable:
    """wrap the widget property setter to first decode then apply a value.

    ``load_fn`` decodes the raw QSettings value -> expected type;

    Special case:  tuples are splatted into positional args for
    multi-argument setters (e.g. ``set_levels(mn, mx)``)
    """
    method = attrgetter(path)(widget)

    def setter(raw: object) -> None:
        value = load_fn(raw)
        if isinstance(value, tuple):
            method(*value)
        else:
            method(value)

    return setter


# dict of properties that should have persistance given a ClassName
#
# Format is:
# Qt class name -> { propKey: (getter, setter, load_fn, save_fn) }
#
# ``getter``/``setter`` are a (possibly dotted) attribute path resolved on the
# widget, each of which must resolve to a bound method.
#
# ``load_fn`` decodes the raw value read from QSettings (IniFormat stores
# everything as a string) back to the type the setter expects.
#
# ``save_fn`` encodes the getter's return value into what is written to
# QSettings, and must yield a string: use ``str`` for scalars and


# Only built-in / third-party classes we do not subclass belong here; every
# widget we own defines ``get_view_saver_properties`` instead.
WIDGET_REGISTRY: dict[str, dict[str, tuple[str, str, Callable, Callable]]] = {
    # QT BASE
    "QTabWidget": {"currentIndex": ("currentIndex", "setCurrentIndex", int, str)},
    "QComboBox": {"currentIndex": ("currentIndex", "setCurrentIndex", int, str)},
    "QGroupBox": {"checked": ("isChecked", "setChecked", _to_bool, str)},
    "QCheckBox": {"checked": ("isChecked", "setChecked", _to_bool, str)},
    "QPushButton": {"checked": ("isChecked", "setChecked", _to_bool, str)},
    "QSplitter": {"state": ("saveState", "restoreState", _identity, _identity)},
    # Imaging (PyDM widget, not subclassed by us)
    "PyDMImageView": {
        "view": ("view.vb.getState", "view.vb.setState", json.loads, _json_dumps),
    },
}

# Registered classes that are also containers of other savable widgets.
CONTAINER_REGISTRY_CLASSES: set[str] = {
    "QSplitter",
    "QTabWidget",
    "QGroupBox",
}


def is_registry_savable(widget: QWidget) -> bool:
    """True if *widget*'s class has fallback properties in ``WIDGET_REGISTRY``."""
    return type(widget).__name__ in WIDGET_REGISTRY


def is_registry_container(widget: QWidget) -> bool:
    """True if *widget*'s class is a registered container of other savables."""
    return type(widget).__name__ in CONTAINER_REGISTRY_CLASSES


def resolve_registry_props(
    widget: QWidget,
) -> dict[str, tuple[Callable, Callable]] | None:
    """Resolve getter/setter callables for each registered property of *widget*.

    Fallback used only for classes without ``get_view_saver_properties`` (see
    module docstring). Returns ``{propKey: (getter, setter)}`` where the getter
    yields a QSettings-storable value and the setter accepts the raw stored
    value, or ``None`` if the class is not registered.
    """
    class_name = type(widget).__name__
    props = WIDGET_REGISTRY.get(class_name)
    if props is None:
        logger.error(f"No registered properties for {class_name}")
        return None
    resolved_props: dict[str, tuple[Callable, Callable]] = {}
    for prop_name, (getter, setter, load_fn, save_fn) in props.items():
        try:
            resolved_props[prop_name] = (
                _make_getter(widget, getter, save_fn),
                _make_setter(widget, setter, load_fn),
            )
        except AttributeError:
            logger.exception(f"ViewSaver: could not resolve {class_name}.{prop_name}, skipping")
    return resolved_props
