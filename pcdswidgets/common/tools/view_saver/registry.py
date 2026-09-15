"""Registry of savable widget properties for ViewSaver."""

import json
import logging
from functools import reduce
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


def _rgetattr(obj: object, path: str) -> object:
    """Nested getattr: ``_rgetattr(w, "a.b")`` is ``w.a.b``.

    Lets a registry entry reach a child widget's own getter/setter
    (e.g. ``roi_multiplier_spinbox.value``) without the parent widget needing
    a dedicated method.
    """
    return reduce(getattr, path.split("."), obj)


def _json_tuple(raw: str) -> tuple:
    """Casts a JSON array to a tuple, so the setter is called with positional args.
    """
    return tuple(json.loads(raw))


def _make_getter(widget: object, path: str, save_fn: Callable) -> Callable:
    """Bind a getter path into a zero-arg callable that returns the encoded value.

    ``save_fn`` turns the widget's value into what QSettings stores, so the
    caller writes ``getter()`` with no serialization knowledge.
    """
    method = _rgetattr(widget, path)
    return lambda: save_fn(method())


def _make_setter(widget: object, path: str, load_fn: Callable) -> Callable:
    """Bind a setter path into a one-arg callable that decodes then applies a value.

    ``load_fn`` decodes the raw QSettings value;

    Special case:  tuples are splatted into positional args for
    multi-argument setters (e.g. ``set_levels(mn, mx)``)
    """
    method = _rgetattr(widget, path)

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
# ``save_fn`` encodes the getter's return value into what is written to
# QSettings, and must yield a string: use ``str`` for scalars and
# ``json.dumps`` for nested dicts/lists. ``_identity`` is used only when the
# value is already a str, or for a ``QByteArray`` (``QSplitter.saveState``),
# which QSettings round-trips natively and must not be stringified.

WIDGET_REGISTRY: dict[
    str, dict[str, tuple[str, str, Callable, Callable]]
] = {
    # QT BASE
    "QTabWidget": {"currentIndex": ("currentIndex", "setCurrentIndex", int, str)},
    "QComboBox": {"currentIndex": ("currentIndex", "setCurrentIndex", int, str)},
    "QGroupBox": {"checked": ("isChecked", "setChecked", _to_bool, str)},
    "QCheckBox": {"checked": ("isChecked", "setChecked", _to_bool, str)},
    "QPushButton": {"checked": ("isChecked", "setChecked", _to_bool, str)},
    "QSplitter": {"state": ("saveState", "restoreState", _identity, _identity)},
    # Imaging
    "EpicsRoiFull": {
        "style": ("get_style_state", "set_style_state", json.loads, json.dumps),
    },
    "CentroidTrackerFull": {
        "threshold": (
            "get_threshold_state",
            "set_threshold_state",
            json.loads,
            json.dumps,
        ),
        "marker_style": (
            "get_marker_style_state",
            "set_marker_style_state",
            json.loads,
            json.dumps,
        ),
        "roi_multiplier": (
            "roi_multiplier_spinbox.value",
            "roi_multiplier_spinbox.setValue",
            float,
            str,
        ),
    },
    "MarkerSelectionFull": {
        "markers": (
            "get_all_marker_states",
            "set_all_marker_states",
            json.loads,
            json.dumps,
        ),
    },
    "ColormapIntesityControlFull": {
        "colormap_index": (
            "colormap_combo.currentIndex",
            "colormap_combo.setCurrentIndex",
            int,
            str,
        ),
        "normalize": (
            "normalize_check.isChecked",
            "normalize_check.setChecked",
            _to_bool,
            str,
        ),
        "levels": ("get_levels", "set_levels", _json_tuple, json.dumps),
    },
    "CollapsibleSection": {
        "collapsed": ("is_collapsed", "set_collapsed", _to_bool, str),
    },
    # Motion
    "MotorTipTiltFull": {
        "horizontal_invert": (
            "horizontal_invert.isChecked",
            "horizontal_invert.setChecked",
            _to_bool,
            str,
        ),
        "vertical_invert": (
            "vertical_invert.isChecked",
            "vertical_invert.setChecked",
            _to_bool,
            str,
        ),
    },
}


def iter_savable_widgets(root: QWidget) -> list[QWidget]:
    """Return every registered-savable descendant of *root*.

    The child tree is walked manually so it stops as soon as a
    widget's class matches WIDGET_REGISTRY

    Non-registered containers are descended
    """
    found: list[QWidget] = []

    def _walk(widget: QWidget) -> None:
        for child in widget.children():
            if not isinstance(child, QWidget):
                continue
            if type(child).__name__ in WIDGET_REGISTRY:
                found.append(child)
                # registered widget = one savable unit; do not descend into it
            else:
                _walk(child)

    _walk(root)
    return found


def discover_widgets(root: QWidget) -> list[str]:
    """Return sorted objectNames of *root*'s savable descendants.

    Widgets without an objectName are skipped (they cannot be keyed in the
    settings file).
    """
    names = [w.objectName() for w in iter_savable_widgets(root) if w.objectName()]
    return sorted(names)


def resolve_widget_props(
    widget: QWidget,
) -> dict[str, tuple[Callable, Callable]] | None:
    """Resolve getter/setter callables for each persisted property of *widget*.

    Returns a mapping ``{propKey: (getter, setter)}`` for the given widget
    instance, or ``None`` if its class has no registered properties.
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
            logger.exception(
                f"ViewSaver: could not resolve {class_name}.{prop_name}, skipping"
            )
    return resolved_props
