"""Registry of savable widget properties for ViewSaver."""

import json
import logging
from functools import reduce
from typing import Callable

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
    """Casts a JSON array to a tuple, so the setter is called with positional args."""
    return tuple(json.loads(raw))


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
    method = _rgetattr(widget, path)
    return lambda: save_fn(method())


def _make_setter(widget: object, path: str, load_fn: Callable) -> Callable:
    """wrap the widget property setter to first decode then apply a value.

    ``load_fn`` decodes the raw QSettings value -> expected type;

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
#
# ``save_fn`` encodes the getter's return value into what is written to
# QSettings, and must yield a string: use ``str`` for scalars and


WIDGET_REGISTRY: dict[str, dict[str, tuple[str, str, Callable, Callable]]] = {
    # QT BASE
    "QTabWidget": {"currentIndex": ("currentIndex", "setCurrentIndex", int, str)},
    "QComboBox": {"currentIndex": ("currentIndex", "setCurrentIndex", int, str)},
    "QGroupBox": {"checked": ("isChecked", "setChecked", _to_bool, str)},
    "QCheckBox": {"checked": ("isChecked", "setChecked", _to_bool, str)},
    "QPushButton": {"checked": ("isChecked", "setChecked", _to_bool, str)},
    "QSplitter": {"state": ("saveState", "restoreState", _identity, _identity)},
    # Imaging
    "PyDMImageView": {
        "view": ("view.vb.getState", "view.vb.setState", json.loads, _json_dumps),
    },
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
        "collapsed": ("get_collapsed", "set_collapsed", _to_bool, str),
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

# Registered classes that are also containers of other savable widgets.
CONTAINER_REGISTRY_CLASSES: set[str] = {
    "QSplitter",
    "QTabWidget",
    "QGroupBox",
    "CollapsibleSection",
}
