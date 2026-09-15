import json
import logging
import os
import subprocess
from collections import namedtuple
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from functools import partial, reduce

import numpy as np
import numpy.typing as npt
from pydm import Display, PyDMChannel
from pydm.widgets import PyDMImageView
from qtpy.QtCore import QEvent, Qt, QTimer
from qtpy.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from pcdswidgets.imaging.common.collapsible_section import CollapsibleSection
from pcdswidgets.imaging.common.epics_roi_full import EpicsRoiFull
from pcdswidgets.imaging.common.centroid_tracker_full import CentroidTrackerFull
from pcdswidgets.imaging.common.marker_selection_full import (
    MarkerSelectionFull,
    NUM_MARKERS,
)
from pcdswidgets.motion.common.motor_style import MotorStyle
from pcdswidgets.motion.common.motor_tip_tilt_full import MotorTipTiltFull
from pcdswidgets.imaging.common.colormap_intesity_control_full import (
    ColormapIntesityControlFull,
)
from nd_plugin_configure import PluginConfigureDialog, build_desired_wiring

logger = logging.getLogger(__name__)

# Number of near/far-field columns (camera + tip-tilt pair); always 1:1.
NUM_FIELDS = 2

# MotorStyle <-> its persistence-key/macro word form. "motor_record" drives
# a standard EPICS motor record (.TWF/.TWR); "smaract" drives a SmarAct
# piezo controller (STEP_FORWARD/STEP_REVERSE). Adding a new motor type
# needs a new MotorStyle member plus an entry here.
_DEFAULT_MOTOR_TYPE = MotorStyle.MotorRecord
_MOTOR_STYLE_NAMES = {
    MotorStyle.MotorRecord: "motor_record",
    MotorStyle.Smaract: "smaract",
}
_MOTOR_TYPE_ALIASES = {name: style for style, name in _MOTOR_STYLE_NAMES.items()}


def _macro_flag(raw: str | bool | None) -> bool:
    """Parse a boolean-ish macro value (e.g. hide_motors), accepting str, bool, or unset."""
    if isinstance(raw, bool):
        return raw
    if not raw:
        return False
    return str(raw).strip().lower() in ("1", "true", "yes")


def _window_title(cam_1: str | None, cam_2: str | None) -> str:
    """Title identifying this instance by its cameras, to tell windows apart.

    The pair usually shares a long PV prefix, so it is shown once. Motors are
    left out - they pair 1:1 with the cameras, and are absent under hide_motors.
    """
    base = "Near/Far Field Alignment"
    if not cam_1 or not cam_2:
        single = cam_1 or cam_2
        return f"{single} - {base}" if single else base

    a, b = cam_1.split(":"), cam_2.split(":")
    shared = 0
    while shared < min(len(a), len(b)) - 1 and a[shared] == b[shared]:
        shared += 1

    if shared:
        cams = f"{':'.join(a[:shared])}:{':'.join(a[shared:])}/{':'.join(b[shared:])}"
    else:
        cams = f"{cam_1} / {cam_2}"
    # Cameras lead: PyDM appends " - PyDM", and task bars truncate the tail.
    return f"{cams} - {base}"


def _resolve_motor_style(raw: str | None) -> MotorStyle | None:
    """Parse a motor_type_N macro value into a MotorStyle.

    Accepts the word form ("smaract"/"motor_record") or MotorStyle's own integer value as a
    string ("0"/"1"). Returns None if raw is empty or matches neither form.
    """
    if not raw:
        return None
    try:
        return MotorStyle(int(raw))
    except (TypeError, ValueError):
        pass
    return _MOTOR_TYPE_ALIASES.get(raw)


# (column index, tab widget attr, column layout attr, section title) for
# each tab group to collapse, one per image view column.
_COLLAPSIBLE_TAB_SECTIONS = (
    (1, "collapsible_tab_1", "col_1", "Imaging Controls"),
    (2, "collapsible_tab_2", "col_2", "Imaging Controls"),
)

# (column index, expert-screen button attr) for each column.
_EXPERT_SCREEN_COLUMNS = (
    (1, "show_expert_button_1"),
    (2, "show_expert_button_2"),
)

# (column index, configure button attr) for each column.
_CONFIGURE_COLUMNS = (
    (1, "configure_button_1"),
    (2, "configure_button_2"),
)

# Default directory for the persisted-settings JSON file;
# the filename itself isn't configurable.
_DEFAULT_CONFIG_DIR = Path.home() / ".config" / "nf_ff_alignment"
_CONFIG_FILENAME = "nf_ff_alignment_settings.json"

# Settings changes are queued and written at most this often, instead of
# once per callback
_SAVE_COALESCE_MS = 120000

# A PyDMChannel's first connection to a brand-new address can silently fail
# (a background CA-plugin task can raise before the PV's chid is populated,
# swallowing the exception); a fresh channel object shortly after takes a
# different, synchronous path that avoids the race - hence retrying.
_LAUNCH_SCRIPT_RETRY_INTERVAL_MS = 2000
_LAUNCH_SCRIPT_MAX_ATTEMPTS = 5


def rgetattr(obj, attr, *args):
    """Nested getattr: rgetattr(obj, "a.b.c") is getattr(getattr(obj, "a"), "b").c, roughly.

    Used to resolve a dotted widget.child.signal_or_method path from a table
    row instead of hardcoding one getattr chain per row.
    """

    def _getattr(obj, attr):
        return getattr(obj, attr, *args)

    return reduce(_getattr, [obj] + attr.split("."))


def decode_char_waveform(waveform: npt.NDArray[np.int8]) -> str:
    """
    Convert an epics char waveform to a string.

    In pyca, these can be loaded into numpy arrays via passing
    numpy=True as a kwarg.

    The waveform is an array of signed 8-bit integers whose
    unsigned representations correspond to the ascii character codes.
    The string is null-terminated.
    """
    # Implementation lifted from PyDM's "parse_value_for_display"
    zeros = np.where(waveform == 0)[0]
    if zeros.size > 0:
        waveform = waveform[: zeros[0]]
    return waveform.tobytes().decode(encoding="ascii", errors="ignore")


@dataclass
class MotorPair:
    """Horizontal/vertical motor PVs for a tip-tilt widget, and whether they're swapped."""

    horizontal_pv: str
    vertical_pv: str
    swapped: bool = False


@dataclass
class ExpertScreenState:
    """Expert-screen script path(s) reported by a camera IOC's LAUNCH_GUI/LAUNCH_EDM PVs."""

    launch_gui_script: str | None = None
    launch_edm_script: str | None = None

    @property
    def script(self) -> str | None:
        """The preferred script to run, if either PV has reported one."""
        return self.launch_gui_script or self.launch_edm_script


class _MainDisplayUI(QWidget):
    """Helper class for typehinting"""

    swap_button_1: QPushButton
    swap_button_2: QPushButton
    flip_h_button_1: QPushButton
    flip_h_button_2: QPushButton
    flip_v_button_1: QPushButton
    flip_v_button_2: QPushButton
    show_expert_button_1: QPushButton
    show_expert_button_2: QPushButton
    configure_button_1: QPushButton
    configure_button_2: QPushButton
    motor_frame_1: QFrame
    motor_frame_2: QFrame
    motor_frame_layout_1: QHBoxLayout
    motor_frame_layout_2: QHBoxLayout
    collapsible_tab_1: QTabWidget
    collapsible_tab_2: QTabWidget
    image_tab_1: QTabWidget
    image_tab_2: QTabWidget
    col_1: QVBoxLayout
    col_2: QVBoxLayout
    image_cam_view_1: PyDMImageView
    image_cam_view_2: PyDMImageView
    image_crop_view_1: PyDMImageView
    image_crop_view_2: PyDMImageView
    marker_selection_1: MarkerSelectionFull
    marker_selection_2: MarkerSelectionFull
    stats_roi_1: EpicsRoiFull
    stats_roi_2: EpicsRoiFull
    crop_roi_1: EpicsRoiFull
    crop_roi_2: EpicsRoiFull
    centroid_tracker_1: CentroidTrackerFull
    centroid_tracker_2: CentroidTrackerFull
    colormap_1: ColormapIntesityControlFull
    colormap_2: ColormapIntesityControlFull


class MainDisplay(Display):
    ui: _MainDisplayUI

    def __init__(
        self,
        parent: QWidget | None = None,
        args: list[str] | None = None,
        macros: dict[str, str] | None = None,
    ):
        if macros is None:
            macros = {}
        self._set_macro_defaults(macros)

        self._config_dir: Path = _DEFAULT_CONFIG_DIR
        # Guards against re-entrant saves while load_settings re-applies
        # values, which re-fires the same signals queue_settings listens on.
        self._loading_settings = False
        # Snapshots waiting to be written, keyed by _config_key.
        self._pending_settings: dict[str, dict] = {}

        super().__init__(parent=parent, args=args, macros=macros)
        self.setWindowTitle(
            _window_title(
                self._macros.get("cam_prefix_1"), self._macros.get("cam_prefix_2")
            )
        )
        logger.debug("Resolved macros: %r", self._macros)
        self._set_config_dir(self._macros.get("config_dir"))
        logger.debug("Using config_dir=%s", self._config_dir)

        self._motors_enabled: bool = not _macro_flag(self._macros.get("hide_motors"))
        self._motor_pairs: dict[int, MotorPair] = self._init_motor_pairs()
        self._expert_screens: dict[int, ExpertScreenState] = {}
        # Kept alive here so the PyDMChannel connections aren't garbage collected
        self._expert_screen_channels: list[PyDMChannel] = []

        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.timeout.connect(self._flush_settings)
        app = QApplication.instance()
        if app is not None:
            # Backstop for quit paths that never close a window, e.g.
            # PyDMMainWindow's File > Quit calling app.quit() directly.
            app.aboutToQuit.connect(self.on_about_to_quit)

        self._configure_motor_widgets()
        self._connect_swap_buttons()
        self._wrap_tabs_in_collapsible_sections()
        self._link_camera_widgets()
        self._init_view_flips()
        self._connect_expert_screen_buttons()
        self._connect_configure_buttons()
        self._connect_persisted_settings()
        self.load_settings()

    def ui_filename(self) -> str:
        return "nf_ff_alignment.ui"

    def ui_filepath(self) -> Path:
        return Path(__file__).resolve().parent / self.ui_filename()

    def on_about_to_quit(self):
        """Flush any pending settings before the application quits."""
        logger.debug("Flushing settings before quit")
        self._flush_settings()

    def showEvent(self, event) -> None:
        """Watch the container window once this display is attached to it."""
        super().showEvent(event)
        window = self.window()
        if window is not None:
            # Qt drops any prior instance of this filter, so re-shows are safe.
            window.installEventFilter(self)

    def eventFilter(self, obj, event) -> bool:
        # PyDM never sends this display a closeEvent - it just reparents it
        # away - so the container window's Close is the only hook that
        # reliably fires while the widgets are still intact.
        if event.type() == QEvent.Close:
            logger.debug("Flushing settings before window close")
            self._flush_settings()
        return super().eventFilter(obj, event)

    def _set_macro_defaults(self, macros: dict[str, str]) -> None:
        """Populate unset macros with sensible defaults."""
        # h_motor_1/2, v_motor_1/2, and cam_prefix_1/2 identify real hardware,
        # so they're deliberately not defaulted - always passed via -m.
        default_map = {
            "cam_roi_prefix_1": ":ROI1:",
            "cam_roi_prefix_2": ":ROI1:",
            "roi_prefix_1": ":ROI2:",
            "roi_prefix_2": ":ROI2:",
            "stat_prefix_1": ":Stats2:",
            "stat_prefix_2": ":Stats2:",
        }
        for name, value in default_map.items():
            macros.setdefault(name, value)
        # config_dir and motor_type_1/2 are left unset here so
        # _set_config_dir/_configure_motor_widgets fall through to their own
        # defaults when no -m override is given.

    def _set_config_dir(self, value: str | None) -> None:
        """Set the persisted-settings directory, falling back to the default on an empty or invalid value.

        An empty value falls back silently. Relative paths and a leading ~ are
        resolved against the cwd; anything that doesn't resolve to an existing
        directory is treated as a mistake, not a request to create one.
        """
        if not value:
            self._config_dir = _DEFAULT_CONFIG_DIR
            return

        path = Path(value).expanduser().resolve()
        if not path.is_dir():
            logger.warning(
                "Invalid config_dir %r (resolved to %s; must be an existing directory) - "
                "falling back to %s",
                value,
                path,
                _DEFAULT_CONFIG_DIR,
            )
            self._config_dir = _DEFAULT_CONFIG_DIR
            return

        self._config_dir = path

    def _init_motor_pairs(self) -> dict[int, MotorPair]:
        """Build motor PV pairs from macros, keyed by tip-tilt widget index (1-based)."""
        pairs = {
            i: MotorPair(
                horizontal_pv=self._macros.get(f"h_motor_{i}"),
                vertical_pv=self._macros.get(f"v_motor_{i}"),
            )
            for i in range(1, NUM_FIELDS + 1)
        }
        for i, pair in pairs.items():
            logger.debug(
                "Column %s motor PVs: horizontal=%r vertical=%r",
                i,
                pair.horizontal_pv,
                pair.vertical_pv,
            )
        return pairs

    def _configure_motor_widgets(self) -> None:
        """Instantiate each column's tip-tilt widget and set it to the right motor_style.

        Resolution order per column: an explicit motor_type_N macro (set via
        -m at launch), falling back to _DEFAULT_MOTOR_TYPE if unset.

        Skipped entirely (frame and swap button hidden instead) when launched
        with hide_motors=true, for setups with no motor control.
        """
        self._tip_tilt_widgets: dict[int, MotorTipTiltFull] = {}
        self._motor_types: dict[int, str] = {}
        if not self._motors_enabled:
            logger.debug("hide_motors set - not building tip-tilt widgets")
            for i in range(1, NUM_FIELDS + 1):
                getattr(self.ui, f"motor_frame_{i}").setVisible(False)
                getattr(self.ui, f"swap_button_{i}").setVisible(False)
            return

        for i in range(1, NUM_FIELDS + 1):
            raw_motor_type = self._macros.get(f"motor_type_{i}")
            style = _resolve_motor_style(raw_motor_type)
            if style is None:
                if raw_motor_type:
                    logger.warning(
                        "Unknown motor type %r for column %s, falling back to %r",
                        raw_motor_type,
                        i,
                        _DEFAULT_MOTOR_TYPE,
                    )
                style = _DEFAULT_MOTOR_TYPE

            frame = getattr(self.ui, f"motor_frame_{i}")
            frame_layout = getattr(self.ui, f"motor_frame_layout_{i}")
            widget = MotorTipTiltFull(parent=frame)
            widget.motor_style = style
            motor_pair = self._motor_pairs[i]
            widget.set_motors(motor_pair.horizontal_pv, motor_pair.vertical_pv)
            frame_layout.addWidget(widget, 0, Qt.AlignHCenter)

            self._motor_types[i] = _MOTOR_STYLE_NAMES[style]
            self._tip_tilt_widgets[i] = widget
            logger.debug(
                "Column %s tip-tilt widget configured: style=%r horizontal=%r vertical=%r",
                i,
                style,
                motor_pair.horizontal_pv,
                motor_pair.vertical_pv,
            )

    def _connect_swap_buttons(self) -> None:
        """Connect all swap buttons to their handlers."""
        if not self._motors_enabled:
            return
        for i in range(1, NUM_FIELDS + 1):
            swap_button = getattr(self.ui, f"swap_button_{i}")
            swap_button.setCheckable(True)
            swap_button.setToolTip(
                "Swap Axis (highlighted when the horizontal/vertical axes are swapped)"
            )
            swap_button.clicked.connect(lambda checked, idx=i: self.swap_motors(idx))

    def _wrap_tabs_in_collapsible_sections(self) -> None:
        """Wrap each column's tab widget in a CollapsibleSection, in place."""
        self._collapsible_sections: dict[int, CollapsibleSection] = {}
        for idx, tab_attr, layout_attr, title in _COLLAPSIBLE_TAB_SECTIONS:
            self._collapsible_sections[idx] = self._wrap_in_collapsible_section(
                getattr(self.ui, tab_attr), getattr(self.ui, layout_attr), title
            )

    @staticmethod
    def _wrap_in_collapsible_section(
        widget: QWidget, layout: QVBoxLayout, title: str
    ) -> CollapsibleSection:
        """Replace *widget* in *layout* with a CollapsibleSection wrapping it, preserving position."""
        index = layout.indexOf(widget)
        layout.removeWidget(widget)
        section = CollapsibleSection(
            widget, title=title, parent=widget.parentWidget(), collapsed=True
        )
        layout.insertWidget(index, section)
        return section

    _CAMERA_WIDGET_NAMES = (
        "marker_selection",
        "stats_roi",
        "crop_roi",
        "centroid_tracker",
        "colormap",
    )

    def _link_camera_widgets(self) -> None:
        """Attach each marker/ROI overlay widget to its own image view."""
        for idx in range(1, NUM_FIELDS + 1):
            parent = SimpleNamespace(
                image_view=getattr(self.ui, f"image_cam_view_{idx}"),
                secondary_image_view=getattr(self.ui, f"image_crop_view_{idx}"),
            )
            for name in self._CAMERA_WIDGET_NAMES:
                getattr(self.ui, f"{name}_{idx}").link_parent_widgets(parent)

    # Both of a column's image views, flipped together so the full-frame and
    # cropped tabs can't disagree about which way the camera is mounted.
    _FLIPPABLE_VIEW_NAMES = ("image_cam_view", "image_crop_view")

    def _column_view_boxes(self, widget_idx: int):
        """Yield the pyqtgraph ViewBox behind each of a column's image views."""
        for name in self._FLIPPABLE_VIEW_NAMES:
            image_view = getattr(self.ui, f"{name}_{widget_idx}")
            try:
                yield image_view.getView().getViewBox()
            except Exception:
                logger.exception("Could not get ViewBox for %s_%s", name, widget_idx)

    def _init_view_flips(self) -> None:
        """Wire each column's Flip H/V buttons to its image views.

        The flip is applied to the pyqtgraph ViewBox (invertX/invertY) rather
        than to the image data, so it only changes how the frame is drawn: the
        marker/ROI/centroid overlays are flipped along with the image because
        they live in the same ViewBox, and every coordinate exchanged with
        EPICS stays in unflipped detector pixels.
        """
        # pyqtgraph's ImageView already inverts y so row 0 draws at the top, so
        # a flip is applied as a delta from whatever each view started out at
        # rather than as an absolute invertX/invertY value.
        self._view_flip_baselines: dict[int, list[tuple]] = {}
        for idx in range(1, NUM_FIELDS + 1):
            self._view_flip_baselines[idx] = [
                (view_box, view_box.xInverted(), view_box.yInverted())
                for view_box in self._column_view_boxes(idx)
            ]
            for axis in ("h", "v"):
                button = getattr(self.ui, f"flip_{axis}_button_{idx}")
                button.toggled.connect(lambda checked, i=idx: self._apply_view_flip(i))

    def _apply_view_flip(self, widget_idx: int) -> None:
        """Mirror a column's image views to match its Flip H/V buttons."""
        flip_x = getattr(self.ui, f"flip_h_button_{widget_idx}").isChecked()
        flip_y = getattr(self.ui, f"flip_v_button_{widget_idx}").isChecked()
        for view_box, base_x, base_y in self._view_flip_baselines[widget_idx]:
            view_box.invertX(base_x != flip_x)
            view_box.invertY(base_y != flip_y)
        logger.debug(
            "Column %s view flip: horizontal=%s vertical=%s",
            widget_idx,
            flip_x,
            flip_y,
        )

    def _connect_expert_screen_buttons(self) -> None:
        """Wire each column's expert-screen button to its camera's LAUNCH_GUI/LAUNCH_EDM PVs."""
        for idx, button_attr in _EXPERT_SCREEN_COLUMNS:
            button = getattr(self.ui, button_attr)
            cam_prefix = self._macros.get(f"cam_prefix_{idx}")

            self._expert_screens[idx] = ExpertScreenState()
            button.setEnabled(False)
            button.clicked.connect(lambda checked, i=idx: self.on_open_expert(i))

            for suffix, attr in (
                (":LAUNCH_GUI", "launch_gui_script"),
                (":LAUNCH_EDM", "launch_edm_script"),
            ):
                self._subscribe_launch_script(idx, attr, f"ca://{cam_prefix}{suffix}")

    def _connect_configure_buttons(self) -> None:
        """Wire each column's Configure button to open its plugin-wiring confirmation dialog."""
        for idx, button_attr in _CONFIGURE_COLUMNS:
            button = getattr(self.ui, button_attr)
            button.clicked.connect(lambda checked, i=idx: self.on_configure(i))

    def on_configure(self, widget_idx: int) -> None:
        """Show the areaDetector plugin-wiring confirmation dialog for a given column."""
        rows = build_desired_wiring(
            cam_prefix=self._macros.get(f"cam_prefix_{widget_idx}"),
            cam_roi_prefix=self._macros.get(f"cam_roi_prefix_{widget_idx}"),
            roi_prefix=self._macros.get(f"roi_prefix_{widget_idx}"),
            stat_prefix=self._macros.get(f"stat_prefix_{widget_idx}"),
        )
        dialog = PluginConfigureDialog(rows, parent=self)
        dialog.exec_()

    # (ui widget name, dotted path from that widget to the signal to persist on) -
    # every entry here is rooted at getattr(self.ui, f"{name}_{idx}").
    _PERSISTED_UI_SIGNALS = (
        ("colormap", "colormap_combo.currentIndexChanged"),
        ("colormap", "normalize_check.toggled"),
        ("colormap", "state_changed"),
        ("centroid_tracker", "roi_multiplier_spinbox.valueChanged"),
        ("centroid_tracker", "state_changed"),
        ("centroid_tracker", "threshold_mode_combo.currentIndexChanged"),
        ("centroid_tracker", "threshold_value_edit.editingFinished"),
        ("marker_selection", "state_changed"),
        ("stats_roi", "state_changed"),
        ("crop_roi", "state_changed"),
        ("flip_h_button", "toggled"),
        ("flip_v_button", "toggled"),
        ("collapsible_tab", "currentChanged"),
        ("image_tab", "currentChanged"),
    )

    def _on_setting_changed(self, widget_idx: int, *_args) -> None:
        """Common slot for every persisted-setting signal, regardless of its arity."""
        self.queue_settings(widget_idx)

    def _connect_persisted_settings(self) -> None:
        """Persist swap/invert/colormap/ROI-multiplier settings whenever the user changes them."""
        for idx in range(1, NUM_FIELDS + 1):
            on_changed = partial(self._on_setting_changed, idx)

            tip_tilt_widget = self._tip_tilt_widgets.get(idx)
            if tip_tilt_widget is not None:
                tip_tilt_widget.horizontal_invert.stateChanged.connect(on_changed)
                tip_tilt_widget.vertical_invert.stateChanged.connect(on_changed)
            self._collapsible_sections[idx].toggled.connect(on_changed)

            for widget_name, signal_path in self._PERSISTED_UI_SIGNALS:
                widget = getattr(self.ui, f"{widget_name}_{idx}")
                rgetattr(widget, signal_path).connect(on_changed)

    def _config_file(self) -> Path:
        return self._config_dir / _CONFIG_FILENAME

    def _config_key(self, widget_idx: int) -> str:
        """A key identifying this column's actual hardware, not its screen slot.

        Keying on the camera/motor PVs (rather than e.g. "column_1") means
        saved settings follow the hardware even if a future launch assigns
        different macros to the near/far-field slots.
        """
        cam_prefix = self._macros.get(f"cam_prefix_{widget_idx}", "")
        h_motor = self._macros.get(f"h_motor_{widget_idx}", "")
        v_motor = self._macros.get(f"v_motor_{widget_idx}", "")
        return f"{cam_prefix}::{h_motor}::{v_motor}"

    # Fields that are a plain get/set round trip. unpack=True splats the
    # stored value into the setter (e.g. set_levels(*v)) instead of passing
    # it as one arg. Fields needing extra logic (swapped, motor-type-dependent
    # invert keys, collapsed, markers) stay explicit below.
    _SettingsField = namedtuple(
        "_SettingsField", "config_key widget_name get_path set_path unpack"
    )
    _SETTINGS_FIELDS = (
        _SettingsField(
            "colormap_index",
            "colormap",
            "colormap_combo.currentIndex",
            "colormap_combo.setCurrentIndex",
            False,
        ),
        _SettingsField(
            "normalize",
            "colormap",
            "normalize_check.isChecked",
            "normalize_check.setChecked",
            False,
        ),
        _SettingsField("levels", "colormap", "get_levels", "set_levels", True),
        _SettingsField(
            "roi_multiplier",
            "centroid_tracker",
            "roi_multiplier_spinbox.value",
            "roi_multiplier_spinbox.setValue",
            False,
        ),
        _SettingsField(
            "centroid_marker_style",
            "centroid_tracker",
            "get_marker_style_state",
            "set_marker_style_state",
            False,
        ),
        _SettingsField(
            "threshold",
            "centroid_tracker",
            "get_threshold_state",
            "set_threshold_state",
            False,
        ),
        _SettingsField(
            "flip_horizontal", "flip_h_button", "isChecked", "setChecked", False
        ),
        _SettingsField(
            "flip_vertical", "flip_v_button", "isChecked", "setChecked", False
        ),
        _SettingsField(
            "active_tab", "collapsible_tab", "currentIndex", "setCurrentIndex", False
        ),
        _SettingsField(
            "active_image_tab", "image_tab", "currentIndex", "setCurrentIndex", False
        ),
        _SettingsField(
            "stats_roi_style", "stats_roi", "get_style_state", "set_style_state", False
        ),
        _SettingsField(
            "crop_roi_style", "crop_roi", "get_style_state", "set_style_state", False
        ),
    )

    def _collect_settings(self, widget_idx: int) -> dict:
        """Snapshot this column's persisted widget state."""
        tip_tilt_widget = self._tip_tilt_widgets.get(widget_idx)
        motor_type = self._motor_types.get(widget_idx)
        marker_widget = getattr(self.ui, f"marker_selection_{widget_idx}")

        settings = {
            "swapped": self._motor_pairs[widget_idx].swapped,
            "collapsed": self._collapsible_sections[widget_idx].is_collapsed(),
            "markers": {
                str(n): marker_widget.get_marker_state(n)
                for n in range(1, NUM_MARKERS + 1)
            },
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        if tip_tilt_widget is not None:
            settings[f"{motor_type}_horizontal_invert"] = (
                tip_tilt_widget.horizontal_invert.isChecked()
            )
            settings[f"{motor_type}_vertical_invert"] = (
                tip_tilt_widget.vertical_invert.isChecked()
            )
        for field in self._SETTINGS_FIELDS:
            widget = getattr(self.ui, f"{field.widget_name}_{widget_idx}")
            settings[field.config_key] = rgetattr(widget, field.get_path)()
        return settings

    def queue_settings(self, widget_idx: int) -> None:
        """Queue this column's settings for the next flush.

        Snapshotting now rather than at flush time keeps the widget reads off
        the shutdown path, where PyDM has already reparented the display away.
        """
        if self._loading_settings:
            return

        try:
            self._pending_settings[self._config_key(widget_idx)] = (
                self._collect_settings(widget_idx)
            )
        except Exception as e:
            logger.warning(f"Failed to read settings for column {widget_idx}: {e}")
            return

        # Coalesce rather than debounce: restarting the timer on every change
        # would starve the write entirely while a signal fires at frame rate.
        if not self._save_timer.isActive():
            self._save_timer.start(_SAVE_COALESCE_MS)

    def _read_configs(self, config_file: Path) -> dict:
        """Read the saved configs, setting the file aside if it is unusable.

        The read happens before every write, so a file this app cannot parse
        would otherwise block all future saves, not just the current one.
        Read errors (permissions, I/O) are left to the caller, since those
        are transient and the file should not be touched.
        """
        if not config_file.exists():
            return {}

        try:
            with open(config_file, "r") as f:
                configs = json.load(f)
        except ValueError as e:  # JSONDecodeError, UnicodeDecodeError
            reason = e
        else:
            if isinstance(configs, dict):
                return configs
            reason = f"expected a JSON object, found {type(configs).__name__}"

        quarantine = config_file.with_suffix(f"{config_file.suffix}.corrupt")
        logger.warning(
            "Config file %s is unusable (%s); moving it to %s and starting over. "
            "Any settings it held for other camera pairs are lost.",
            config_file,
            reason,
            quarantine,
        )
        try:
            os.replace(config_file, quarantine)
        except OSError as e:
            logger.warning("Could not move %s aside: %s", config_file, e)
        return {}

    def _flush_settings(self) -> None:
        """Merge every queued column into the config file in one atomic write."""
        self._save_timer.stop()
        if not self._pending_settings:
            return

        try:
            config_file = self._config_file()
            all_configs = self._read_configs(config_file)

            # Re-read and merge on every flush so a concurrent instance's keys
            # survive; only the keys this instance owns are replaced.
            all_configs.update(self._pending_settings)

            config_file.parent.mkdir(parents=True, exist_ok=True)
            # Unique per process: a shared temp name lets another instance
            # truncate this one mid-write, promoting a partial file over the config.
            tmp_file = config_file.with_suffix(
                f"{config_file.suffix}.{os.getpid()}.tmp"
            )
            try:
                with open(tmp_file, "w") as f:
                    json.dump(all_configs, f, indent=2)
                os.replace(tmp_file, config_file)
            except BaseException:
                # A per-pid temp is never reused by the next writer.
                tmp_file.unlink(missing_ok=True)
                raise

            logger.debug("Settings saved for %s", ", ".join(self._pending_settings))
            self._pending_settings.clear()

        except Exception as e:
            # Left pending on purpose, so the next flush retries them.
            logger.warning(f"Failed to save settings: {e}")

    def load_settings(self) -> None:
        """Load and apply saved settings for every column, if a config file exists."""
        config_file = self._config_file()
        if not config_file.exists():
            logger.info(f"No config file found at {config_file}, using defaults")
            return

        self._loading_settings = True
        try:
            all_configs = self._read_configs(config_file)

            for idx in range(1, NUM_FIELDS + 1):
                config = all_configs.get(self._config_key(idx))
                if config is None:
                    continue

                if bool(config.get("swapped", False)) != self._motor_pairs[idx].swapped:
                    self.swap_motors(idx)

                tip_tilt_widget = self._tip_tilt_widgets.get(idx)
                motor_type = self._motor_types.get(idx)
                if tip_tilt_widget is not None:
                    if f"{motor_type}_horizontal_invert" in config:
                        tip_tilt_widget.horizontal_invert.setChecked(
                            config[f"{motor_type}_horizontal_invert"]
                        )
                    if f"{motor_type}_vertical_invert" in config:
                        tip_tilt_widget.vertical_invert.setChecked(
                            config[f"{motor_type}_vertical_invert"]
                        )

                for field in self._SETTINGS_FIELDS:
                    if field.config_key not in config:
                        continue
                    widget = getattr(self.ui, f"{field.widget_name}_{idx}")
                    setter = rgetattr(widget, field.set_path)
                    if field.unpack:
                        setter(*config[field.config_key])
                    else:
                        setter(config[field.config_key])

                if "collapsed" in config:
                    self._collapsible_sections[idx].set_collapsed(config["collapsed"])

                marker_widget = getattr(self.ui, f"marker_selection_{idx}")
                for marker_number, marker_state in config.get("markers", {}).items():
                    marker_widget.set_marker_state(int(marker_number), marker_state)

                if "stats_roi_style" in config:
                    getattr(self.ui, f"stats_roi_{idx}").set_style_state(
                        config["stats_roi_style"]
                    )
                if "crop_roi_style" in config:
                    getattr(self.ui, f"crop_roi_{idx}").set_style_state(
                        config["crop_roi_style"]
                    )

                logger.info(
                    f"Loaded settings for column {idx} ({self._config_key(idx)})"
                )

        except Exception as e:
            logger.warning(f"Failed to load settings: {e}")
        finally:
            self._loading_settings = False

    def _subscribe_launch_script(
        self, widget_idx: int, attr: str, address: str, attempt: int = 1
    ) -> None:
        """Open a PyDMChannel to a LAUNCH_GUI/LAUNCH_EDM PV, retrying with a fresh channel if needed.

        See the comment above _LAUNCH_SCRIPT_RETRY_INTERVAL_MS for why a retry is necessary.
        """
        logger.debug(
            "Column %s: connecting %s channel to %r (attempt %s/%s)",
            widget_idx,
            attr,
            address,
            attempt,
            _LAUNCH_SCRIPT_MAX_ATTEMPTS,
        )
        channel = PyDMChannel(
            address=address,
            value_slot=partial(self._on_launch_script_received, widget_idx, attr),
        )
        channel.connect()
        self._expert_screen_channels.append(channel)

        if attempt >= _LAUNCH_SCRIPT_MAX_ATTEMPTS:
            logger.debug(
                "Column %s: giving up retrying %s channel %r after %s attempts",
                widget_idx,
                attr,
                address,
                attempt,
            )
            return

        def retry_if_still_missing() -> None:
            if getattr(self._expert_screens[widget_idx], attr) is None:
                logger.debug(
                    "Column %s: %s channel %r still not connected, retrying",
                    widget_idx,
                    attr,
                    address,
                )
                self._subscribe_launch_script(
                    widget_idx, attr, address, attempt=attempt + 1
                )

        QTimer.singleShot(_LAUNCH_SCRIPT_RETRY_INTERVAL_MS, retry_if_still_missing)

    def _on_launch_script_received(
        self, widget_idx: int, attr: str, value: npt.NDArray[np.int8]
    ) -> None:
        """Decode an incoming LAUNCH_GUI/LAUNCH_EDM char waveform and store it for later use."""
        try:
            script = decode_char_waveform(value)
        except Exception:
            logger.exception(
                "Error decoding expert screen script for column %s", widget_idx
            )
            return
        logger.debug("Column %s: received %s = %r", widget_idx, attr, script)
        setattr(self._expert_screens[widget_idx], attr, script)
        getattr(self.ui, f"show_expert_button_{widget_idx}").setEnabled(True)

    def on_open_expert(self, widget_idx: int) -> None:
        """Open the expert screen script reported by the camera IOC for a given column."""
        script = self._expert_screens[widget_idx].script
        if not script:
            QMessageBox.critical(
                self,
                "Error",
                "No expert screen available, PVs did not connect.",
                QMessageBox.Ok,
                QMessageBox.Ok,
            )
            return
        logger.info("Running %s", script)
        # Not handling other errors for now
        subprocess.run([script])

    def swap_motors(self, widget_idx: int) -> None:
        """Swap the motor assignments for a specific column's active tip-tilt widget.

        Args:
            widget_idx: Index of the column (1-based)
        """
        if widget_idx not in self._tip_tilt_widgets:
            return

        motor_pair = self._motor_pairs[widget_idx]
        motor_pair.swapped = not motor_pair.swapped

        tip_tilt_widget = self._tip_tilt_widgets[widget_idx]
        if motor_pair.swapped:
            tip_tilt_widget.set_motors(motor_pair.vertical_pv, motor_pair.horizontal_pv)
        else:
            tip_tilt_widget.set_motors(motor_pair.horizontal_pv, motor_pair.vertical_pv)

        # Set explicitly rather than relying on the button's own click-toggle,
        # since load_settings calls this directly with no click involved.
        getattr(self.ui, f"swap_button_{widget_idx}").setChecked(motor_pair.swapped)
