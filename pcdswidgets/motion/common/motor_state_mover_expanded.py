"""
Expanded motor state mover (variant 2).

A self-contained replacement for the Typhos expert screen (no Typhos dependency):
the plain :class:`MotorStateMover` on top (with its own Expert Screen button
hidden -- we are already in the expert screen), then a tab group with

* **Normal** -- always present: the raw device signals (busy, done, error,
  error_id, error_message, reset_cmd), matching the plain state-mover expert
  screen.
* **Configuration** -- shown *only* when the caller provides both ``stateCount``
  and ``deviceTokens`` (the plain expert screen has no config tab; the configured
  one does). A read-only per-state config grid whose size is driven by two
  properties instead of a fixed .ui:

  - ``stateCount`` -- number of states (grid rows).
  - ``deviceTokens`` -- comma-separated per-device tokens (grid columns). The
    tokens are device specific (e.g. ``D1M1,D3M1``) and cannot be generated from a
    count, so they are listed explicitly. ``device_count`` == number of tokens.
* **Diagnostics** -- shown when the device and ``deviceTokens`` are provided
  (both variants). A per-motor grid (one row per token, in order) of the
  transit breakdown from ``FB_PositionStateReadND``: ``MOVING`` and ``STATUS``
  (AT_STATE / IN_TRANSIT / UNKNOWN; STATUS already covers the at-state case).
  The STATUS bar turns red while that motor's axis error
  (``ca://{device}:{token}:bError_RBV``) is set. Each row also has a cog
  button that runs ``pcdswidgets-show MotorClassicRow --motor {device}:{token}
  --motor_type {motorType}``; ``motorType`` (GENERIC, IMS, BECKHOFF or
  BECKHOFF_LEGACY, default BECKHOFF) picks which expert screen that row's own
  button then opens.

Everything here is read-only display (plus the reset command). Config cells
resolve to::

    ca://{motor}:STATE:{token}:{NN}:{leaf}_RBV

with ``{NN}`` the zero-padded 2-digit state index and ``{leaf}`` one of
``NAME`` or ``SETPOINT``. Diagnostics cells resolve to::

    ca://{motor}:{leaf}:{NN}_RBV

with ``{NN}`` the zero-padded 2-digit motor index (position in ``deviceTokens``,
from 1) and ``{leaf}`` one of ``MOVING`` or ``STATUS``.
"""

from __future__ import annotations

from pydm.utilities import IconFont
from pydm.widgets.channel import PyDMChannel
from pydm.widgets.display_format import DisplayFormat
from pydm.widgets.enum_combo_box import PyDMEnumComboBox
from pydm.widgets.label import PyDMLabel
from pydm.widgets.pushbutton import PyDMPushButton
from pydm.widgets.shell_command import PyDMShellCommand
from qtpy import QtCore, QtGui, QtWidgets

from pcdswidgets.motion.common.motor_state_mover import MotorStateMover

try:
    from qtpy.QtCore import pyqtProperty
except ImportError:  # PySide fallback
    from qtpy.QtCore import Property as pyqtProperty  # type: ignore

# palette shared with the plain state mover
_SLATE = "rgb(52, 73, 94)"
_MUTE = "rgb(125, 125, 125)"
_CELL_TXT = "rgb(51, 51, 51)"
_CELL_BG = "rgb(244, 244, 244)"
_CELL_BD = "rgb(201, 201, 201)"

# boolean-bar colors: Typhos blue when set, grey when clear (matches the plain
# state mover's moving LED). The error bar toggles blue (clear) / red (set), and
# the error message turns red only while the error flag is set.
_BAR_ON = "rgb(20, 100, 239)"
_BAR_ON_HOVER = "rgb(15, 80, 200)"
_BAR_OFF = "rgb(150, 150, 150)"
_BAR_RED = "rgb(220, 40, 40)"

# "Normal" tab device signals: (row label, PV suffix under ${MOTOR}, kind).
# kind: "led" -> boolean bar, blue (set) / grey (clear);
#       "error_led" -> boolean bar, red (set) / blue (clear);
#       "text" -> numeric text;
#       "error_msg" -> char waveform decoded as a string, red while ERR is set.
_NORMAL_SIGNALS = (
    ("busy", "STATE:BUSY_RBV", "led"),
    ("done", "STATE:DONE_RBV", "led"),
    ("error", "STATE:ERR_RBV", "error_led"),
    ("error_id", "STATE:ERRID_RBV", "led"),
    ("error_message", "STATE:ERRMSG_RBV", "error_msg"),
)
_ERROR_SUFFIX = "STATE:ERR_RBV"
_RESET_SUFFIX = "STATE:RESET"

# "Diagnostics" tab per-motor columns: (header, PV leaf under ${DEVICE}:, kind).
# Each cell resolves to ca://{device}:{leaf}:{NN}_RBV with {NN} the
# zero-padded motor index (position in deviceTokens, starting at 1).
_DIAG_COLUMNS = (
    ("Moving", "MOVING", "bool"),
    ("Status", "STATUS", "status"),
)
# E_MotorTransitStatus values -> bar color
_TRANSIT_COLORS = {0: "rgb(224, 138, 20)", 1: "rgb(46, 160, 67)", 2: _BAR_ON}
# per-motor axis error flag: ca://{device}:{token}:bError_RBV (red status bar while set)
_AXIS_ERROR_LEAF = "bError_RBV"
# Motor types understood by MotorClassicRow (selects its expert-screen command)
_MOTOR_TYPES = ("GENERIC", "IMS", "BECKHOFF", "BECKHOFF_LEGACY")

# PMPS variant Configuration rows: (row label, PV suffix under ${DEVICE}).
# Each row shows a value readback (ca://{device}:{suffix}_RBV) and a setpoint
# selector (ca://{device}:{suffix}). Confirm the suffixes against the IOC.
_PMPS_ROWS = (
    ("arb_enable", "STATE:PMPS:ARB:ENABLE"),
    ("maint_mode", "STATE:PMPS:MAINT"),
)

# fixed width of the plain state mover (matches the Form width in
# motor_state_mover.ui) so the expert's top row keeps the plain screen's size
_PLAIN_MOVER_WIDTH = 680
# height of the GET/SET widgets in motor_state_mover.ui -- the Clear Error button
# is matched to this once it moves onto the main row in the expert
_MAIN_ROW_HEIGHT = 46

_TAB_STYLE = (
    "QTabWidget::pane { border: 1px solid rgb(207, 214, 220); border-radius: 6px;"
    " top: -1px; background: rgb(251, 252, 253); }"
    "QTabBar::tab { background: rgb(233, 237, 240); color: rgb(125, 125, 125);"
    " padding: 6px 18px; border: 1px solid rgb(207, 214, 220); border-bottom: none;"
    " border-top-left-radius: 6px; border-top-right-radius: 6px; margin-right: 2px; }"
    f"QTabBar::tab:selected {{ background: rgb(251, 252, 253); color: {_SLATE}; }}"
)


class _TabPage(QtWidgets.QWidget):
    """Tab page that reports its own natural height only while it is the current
    page, so a hidden page never inflates the tab widget's size."""

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.active = False

    def sizeHint(self) -> QtCore.QSize:
        hint = super().sizeHint()
        return hint if self.active else QtCore.QSize(hint.width(), 0)

    def minimumSizeHint(self) -> QtCore.QSize:
        hint = super().minimumSizeHint()
        return hint if self.active else QtCore.QSize(hint.width(), 0)


class _CurrentPageTabWidget(QtWidgets.QTabWidget):
    """QTabWidget made of :class:`_TabPage` pages that sizes to the visible page
    rather than the tallest one, so the short Normal tab doesn't reserve the
    Configuration tab's height (which grows further in the PMPS variant)."""

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.currentChanged.connect(self._sync_active_page)

    def tabInserted(self, index: int) -> None:
        super().tabInserted(index)
        self._sync_active_page()

    def tabRemoved(self, index: int) -> None:
        super().tabRemoved(index)
        self._sync_active_page()

    def _sync_active_page(self, *_args) -> None:
        current = self.currentWidget()
        for i in range(self.count()):
            page = self.widget(i)
            page.active = page is current
            page.updateGeometry()
        self.updateGeometry()


class MotorStateMoverExpanded(QtWidgets.QFrame):
    """Plain state mover + a read-only, dynamically sized state-config grid."""

    # Plain QFrame (not a DesignerWidget), so PyDM reads _qt_designer_ directly.
    _qt_designer_ = {
        "group": "ECS Motion Common",
        "is_container": False,
    }

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self._device = ""
        self._state_count = 0
        self._state_start = 1
        self._device_tokens = ""
        self._motor_type = "BECKHOFF"

        self._outer = QtWidgets.QVBoxLayout(self)
        self._outer.setContentsMargins(8, 8, 8, 8)
        self._outer.setSpacing(8)

        # plain state mover on top, always visible (reused verbatim, minus its
        # own Expert Screen button -- we are already inside the expert screen --
        # and its error message, which the Normal tab already shows)
        self.plainMover = MotorStateMover(self)
        expert_btn = getattr(self.plainMover, "expertScreenButton", None)
        if expert_btn is not None:
            expert_btn.hide()
        error_status = getattr(self.plainMover, "errorStatus", None)
        if error_status is not None:
            error_status.hide()
        # move Clear Error up onto the main row, in line with the GET/SET widgets
        # (its own status row is now empty -- error message lives in the Normal tab)
        clear_btn = getattr(self.plainMover, "clearErrorButton", None)
        if clear_btn is not None and hasattr(self.plainMover, "mainRow"):
            clear_btn.setFixedHeight(_MAIN_ROW_HEIGHT)  # match the GET/SET height
            self.plainMover.mainRow.addWidget(clear_btn)
        status_row = getattr(self.plainMover, "statusRow", None)
        if status_row is not None:
            for i in reversed(range(status_row.count())):
                if status_row.itemAt(i).spacerItem() is not None:
                    status_row.takeAt(i)  # drop the leftover spacer so the row collapses
        # keep the plain mover at the plain screen's fixed width so the GET/SET
        # widgets stay the same size (and don't stretch to the config grid width)
        self.plainMover.setFixedWidth(_PLAIN_MOVER_WIDTH)
        top_row = QtWidgets.QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.addWidget(self.plainMover)
        top_row.addStretch(1)
        self._outer.addLayout(top_row)

        self.tabs = _CurrentPageTabWidget(self)
        self.tabs.setStyleSheet(_TAB_STYLE)

        # "Normal" tab: always present -- the raw device signals
        self._normal_tab = _TabPage()
        self._normal_layout = QtWidgets.QVBoxLayout(self._normal_tab)
        self._normal_layout.setContentsMargins(14, 14, 14, 14)
        self.tabs.addTab(self._normal_tab, "Normal")

        # "Configuration" tab: built here but attached only when state_count and
        # device tokens are provided by the caller (see _sync_tabs)
        self._config_tab = _TabPage()
        self._config_layout = QtWidgets.QVBoxLayout(self._config_tab)
        self._config_layout.setContentsMargins(12, 12, 12, 12)

        # "Diagnostics" tab: per-motor transit breakdown, attached only when
        # device tokens are provided (see _sync_tabs)
        self._diag_tab = _TabPage()
        self._diag_layout = QtWidgets.QVBoxLayout(self._diag_tab)
        self._diag_layout.setContentsMargins(12, 12, 12, 12)

        self._outer.addWidget(self.tabs)
        self._rebuild_normal()
        self._rebuild_grid()
        self.tabs.currentChanged.connect(self._on_tab_changed)

    def _on_tab_changed(self, _index: int) -> None:
        self.tabs.updateGeometry()
        self._fit_window_height()

    def _relayout_to_window(self, win: QtWidgets.QWidget) -> None:
        """Synchronously invalidate and re-activate every layout between the tabs
        and the window. Relying on posted LayoutRequest events is not enough: the
        invalidation climbs one level per event round, so the window's minimum
        height would still be the previous tab's when we resize."""
        chain = []
        widget = self.tabs
        while widget is not None:
            chain.append(widget)
            if widget is win:
                break
            widget = widget.parentWidget()
        for widget in chain:
            if widget.layout() is not None:
                widget.layout().invalidate()
        for widget in chain:
            if widget.layout() is not None:
                widget.layout().activate()

    def _fit_window_height(self) -> None:
        win = self.window()
        if win.isMaximized() or win.isFullScreen():
            return
        # Do the whole relayout + resize synchronously with painting suspended so
        # the intermediate (cropped / oversized) state is never shown.
        win.setUpdatesEnabled(False)
        try:
            self._relayout_to_window(win)
            win.resize(win.width(), win.height() + self.sizeHint().height() - self.height())
            self._relayout_to_window(win)
        finally:
            win.setUpdatesEnabled(True)

    # props
    def get_device(self) -> str:
        return self._device

    def set_device(self, value: str) -> None:
        self._device = value
        self.plainMover.setProperty("device", value)
        self._rebuild_normal()
        self._rebuild_grid()

    device = pyqtProperty(str, get_device, set_device)

    def get_state_count(self) -> int:
        return self._state_count

    def set_state_count(self, value: int) -> None:
        self._state_count = max(0, int(value))
        self._rebuild_grid()

    stateCount = pyqtProperty(int, get_state_count, set_state_count)

    def get_state_start(self) -> int:
        return self._state_start

    def set_state_start(self, value: int) -> None:
        self._state_start = int(value)
        self._rebuild_grid()

    stateStartIndex = pyqtProperty(int, get_state_start, set_state_start)

    def get_device_tokens(self) -> str:
        return self._device_tokens

    def set_device_tokens(self, value: str) -> None:
        self._device_tokens = value
        self._rebuild_grid()

    deviceTokens = pyqtProperty(str, get_device_tokens, set_device_tokens)

    def get_motor_type(self) -> str:
        return self._motor_type

    def set_motor_type(self, value: str) -> None:
        value = str(value).strip().upper()
        self._motor_type = value if value in _MOTOR_TYPES else "BECKHOFF"
        self._rebuild_diag()

    # MotorClassicRow motor type used by the Diagnostics cog buttons
    motorType = pyqtProperty(str, get_motor_type, set_motor_type)

    # build
    @property
    def _tokens(self) -> list[str]:
        return [t.strip() for t in self._device_tokens.split(",") if t.strip()]

    def _channel(self, token: str, index: int, leaf: str) -> str:
        return f"ca://{self._device}:STATE:{token}:{index:02d}:{leaf}_RBV"

    @staticmethod
    def _clear_layout(layout: QtWidgets.QLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)  # remove from view now; deleteLater is async
                widget.deleteLater()

    def _rebuild_normal(self) -> None:
        self._clear_layout(self._normal_layout)

        panel = QtWidgets.QWidget()
        form = QtWidgets.QGridLayout(panel)
        form.setContentsMargins(0, 0, 0, 0)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(6)
        form.setColumnStretch(1, 1)

        error_channel = f"ca://{self._device}:{_ERROR_SUFFIX}"
        row = 0
        for label, suffix, kind in _NORMAL_SIGNALS:
            form.addWidget(_row_label(label), row, 0)
            channel = f"ca://{self._device}:{suffix}"
            if kind == "led":
                # non-error signals stay blue by default (Typhos-style)
                widget = _bool_bar(channel, on_color=_BAR_ON, off_color=_BAR_ON)
            elif kind == "error_led":
                widget = _bool_bar(channel, on_color=_BAR_RED, off_color=_BAR_ON)
            elif kind == "error_msg":
                widget = _error_message(channel, error_channel)
            else:  # text
                widget = _signal_value(channel)
            form.addWidget(widget, row, 1)
            row += 1

        # reset_cmd: the command button, kept but with no (redundant) label text
        form.addWidget(_row_label("reset_cmd"), row, 0)
        form.addWidget(_command_button(f"ca://{self._device}:{_RESET_SUFFIX}"), row, 1)

        self._normal_layout.addWidget(panel)
        self._normal_layout.addStretch(1)

    def _config_provided(self) -> bool:
        """The Configuration tab only exists when the caller supplies both."""
        return self._state_count > 0 and bool(self._tokens)

    def _diag_provided(self) -> bool:
        """The Diagnostics tab needs the device prefix and the motor tokens."""
        return bool(self._device) and bool(self._tokens)

    def _sync_tabs(self) -> None:
        """Attach/detach the optional tabs, keeping Normal / Configuration /
        Diagnostics order."""
        self._rebuild_diag()
        idx = self.tabs.indexOf(self._config_tab)
        if self._config_provided():
            if idx == -1:
                self.tabs.insertTab(1, self._config_tab, "Configuration")
        elif idx != -1:
            self.tabs.removeTab(idx)  # detach (does not delete the widget)

        idx = self.tabs.indexOf(self._diag_tab)
        if self._diag_provided():
            if idx == -1:
                self.tabs.addTab(self._diag_tab, "Diagnostics")
        elif idx != -1:
            self.tabs.removeTab(idx)
        self.tabs.updateGeometry()

    def _rebuild_diag(self) -> None:
        self._clear_layout(self._diag_layout)
        if not self._diag_provided():
            return

        box = QtWidgets.QWidget()
        grid = QtWidgets.QGridLayout(box)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(6)

        for col, (title, _leaf, _kind) in enumerate(_DIAG_COLUMNS, start=1):
            header = _hdr(title, sub=True)
            header.setFixedHeight(22)
            grid.addWidget(header, 0, col)
            grid.setColumnStretch(col, 1)

        for r, token in enumerate(self._tokens):
            grid.addWidget(_row_label(token), r + 1, 0)
            for col, (_title, leaf, kind) in enumerate(_DIAG_COLUMNS, start=1):
                channel = f"ca://{self._device}:{leaf}:{r + 1:02d}_RBV"
                if kind == "bool":
                    widget = _bool_bar(channel, on_color=_BAR_ON, off_color=_BAR_OFF)
                else:
                    # a set axis error turns the status bar red whatever the status is
                    widget = _status_bar(channel, _axis_error_channel(self._device, token))
                grid.addWidget(widget, r + 1, col)
            grid.addWidget(
                _expert_button(f"{self._device}:{token}", self._motor_type), r + 1, len(_DIAG_COLUMNS) + 1
            )

        self._diag_layout.addWidget(_group("Per-Motor Diagnostics", box))
        self._diag_layout.addStretch(1)

    def _build_state_grid(self) -> QtWidgets.QGroupBox | None:
        """"States" frame holding the scrollable per-state grid (state name |
        "<motor>: SetPoint" x N), or None when no state count / tokens were supplied."""
        tokens = self._tokens
        if not (self._state_count > 0 and tokens):
            return None

        box = QtWidgets.QWidget()
        grid = QtWidgets.QGridLayout(box)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(5)

        # header row: one "<motor>: SetPoint" column per device token; the state
        # column is fixed, the setpoint columns share the remaining width equally
        for col, token in enumerate(tokens, start=1):
            header = _hdr(f"{token}: SetPoint", sub=True)
            header.setFixedHeight(22)
            grid.addWidget(header, 0, col)
            grid.setColumnStretch(col, 1)
        # absorb extra height below the last state so rows stay compact
        grid.setRowStretch(self._state_count + 1, 1)

        for r in range(self._state_count):
            index = self._state_start + r
            row = r + 1
            # state name: read from the first device token (char waveform -> string)
            name = _cell_label(
                self._channel(tokens[0], index, "NAME"),
                bold=True,
                align=QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter,
                as_string=True,
            )
            grid.addWidget(name, row, 0)

            for col, token in enumerate(tokens, start=1):
                grid.addWidget(_cell_label(self._channel(token, index, "SETPOINT")), row, col)

        # up to ~15 states per motor: keep the tab compact and scroll instead
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        scroll.setMinimumHeight(120)
        scroll.setStyleSheet(
            "QScrollArea { background: transparent; border: none; }"
            "QScrollArea > QWidget > QWidget { background: transparent; }"
        )
        scroll.setWidget(box)
        return _group("States", scroll)

    def _rebuild_grid(self) -> None:
        self._clear_layout(self._config_layout)
        if not self._config_provided():
            self._sync_tabs()
            return

        box = self._build_state_grid()
        if box is not None:
            self._config_layout.addWidget(box, 1)
        self._sync_tabs()


class MotorStateMoverExpandedPMPS(MotorStateMoverExpanded):
    """PMPS variant: the Configuration tab holds the PMPS controls (arb_enable,
    maint_mode) -- each a value readback plus a setpoint selector, sharing the
    ${DEVICE} prefix -- with the per-state motor grid shown below them (when
    state count / tokens are supplied)."""

    def _config_provided(self) -> bool:
        # the PMPS controls only need the device prefix (no state count / tokens)
        return bool(self._device)

    def _build_pmps_box(self) -> QtWidgets.QGroupBox:
        box = QtWidgets.QWidget()
        grid = QtWidgets.QGridLayout(box)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(6)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(2, 1)

        for r, (label, suffix) in enumerate(_PMPS_ROWS):
            grid.addWidget(_row_label(label), r, 0)
            grid.addWidget(_bool_bar(f"ca://{self._device}:{suffix}_RBV", on_color=_BAR_ON, off_color=_BAR_ON), r, 1)
            grid.addWidget(_setpoint_combo(f"ca://{self._device}:{suffix}"), r, 2)

        return _group("PMPS", box)

    def _rebuild_grid(self) -> None:
        self._clear_layout(self._config_layout)
        if not self._config_provided():
            self._sync_tabs()
            return

        self._config_layout.addWidget(self._build_pmps_box())

        # per-state settings shown below the PMPS controls, for consistency with
        # the standard expert (only when state count / tokens are supplied)
        state_box = self._build_state_grid()
        if state_box is not None:
            self._config_layout.addSpacing(4)
            self._config_layout.addWidget(state_box, 1)
        else:
            self._config_layout.addStretch(1)
        self._sync_tabs()


# helpers
def _group(title: str, content: QtWidgets.QWidget) -> QtWidgets.QGroupBox:
    """Titled frame around ``content``."""
    group = QtWidgets.QGroupBox(title)
    group.setFont(_bold(10))
    group.setStyleSheet(
        f"QGroupBox {{ color: {_SLATE}; border: 1px solid rgb(207, 214, 220); border-radius: 6px;"
        " margin-top: 10px; padding-top: 6px; background: transparent; }"
        "QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left;"
        " left: 12px; padding: 0 6px; }"
    )
    layout = QtWidgets.QVBoxLayout(group)
    layout.setContentsMargins(8, 8, 8, 8)
    layout.addWidget(content)
    return group


def _plain(size: int) -> QtGui.QFont:
    return QtGui.QFont("DejaVu Sans", size)


def _bold(size: int) -> QtGui.QFont:
    f = QtGui.QFont("DejaVu Sans", size)
    f.setBold(True)
    return f


def _hdr(text: str, sub: bool = False) -> QtWidgets.QLabel:
    lab = QtWidgets.QLabel(text)
    lab.setAlignment(QtCore.Qt.AlignCenter)
    lab.setFont(_bold(9 if sub else 10))
    lab.setStyleSheet(f"color: {_MUTE if sub else _SLATE}; background: transparent;")
    return lab


def _cell_label(channel: str, bold: bool = False, align=QtCore.Qt.AlignCenter, as_string: bool = False) -> PyDMLabel:
    lab = PyDMLabel()
    lab.setFont(_bold(10) if bold else _plain(10))
    lab.setFixedHeight(28)
    lab.setMinimumWidth(80)
    lab.setAlignment(align)
    lab.showUnits = True
    if as_string:
        # NAME_RBV is a char waveform; decode it to a string instead of showing
        # the raw array of character codes.
        lab.displayFormat = DisplayFormat.String
    lab.setStyleSheet(
        f"PyDMLabel {{ color: {_CELL_TXT}; background: {_CELL_BG};"
        f" border: 1px solid {_CELL_BD}; border-radius: 4px; padding: 0 8px; }}"
    )
    lab.channel = channel
    return lab


def _row_label(text: str) -> QtWidgets.QLabel:
    lab = QtWidgets.QLabel(text)
    lab.setFont(_bold(10))
    lab.setMinimumWidth(100)
    lab.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
    lab.setStyleSheet(f"color: {_SLATE}; background: transparent;")
    return lab


def _signal_value(channel: str) -> PyDMLabel:
    lab = PyDMLabel()
    lab.setFont(_plain(10))
    lab.setMinimumHeight(26)
    lab.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
    lab.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
    lab.setStyleSheet(
        f"PyDMLabel {{ color: {_CELL_TXT}; background: {_CELL_BG};"
        f" border: 1px solid {_CELL_BD}; border-radius: 4px; padding: 2px 10px; }}"
    )
    lab.channel = channel
    return lab


class _BoolBar(PyDMLabel):
    """Full-width rounded bar (Typhos-style) with the value shown as text.
    Background is ``on_color`` when the value is set, ``off_color`` when clear."""

    def __init__(
        self,
        on_color: str = _BAR_ON,
        off_color: str = _BAR_OFF,
        parent: QtWidgets.QWidget | None = None,
    ):
        super().__init__(parent)
        self._on_color = on_color
        self._off_color = off_color
        self.setFont(_bold(10))
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setMinimumHeight(26)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.alarmSensitiveContent = False
        self.alarmSensitiveBorder = False
        self._paint(False)

    def _paint(self, on: bool) -> None:
        self.setStyleSheet(
            f"PyDMLabel {{ color: white; background: {self._on_color if on else self._off_color};"
            f" border: 1px solid rgba(0, 0, 0, 40); border-radius: 8px; }}"
        )

    def value_changed(self, new_value) -> None:
        super().value_changed(new_value)  # renders the value text
        self._paint(bool(new_value))


class _StatusBar(PyDMLabel):
    """Enum text (``E_MotorTransitStatus``) on a rounded bar colored by value:
    AT_STATE green, IN_TRANSIT blue, UNKNOWN amber (the "stopped mid-transit"
    symptom this tab exists to expose). While the motor's axis error flag
    (``error_channel``) is set the bar is red regardless of the status."""

    def __init__(self, error_channel: str = "", parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.setFont(_bold(10))
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setMinimumHeight(26)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.alarmSensitiveContent = False
        self.alarmSensitiveBorder = False
        self._status = None
        self._axis_error = False
        self._paint()

        if error_channel:
            self._error_chan = PyDMChannel(address=error_channel, value_slot=self._error_changed)
            self._error_chan.connect()
            chan = self._error_chan
            self.destroyed.connect(lambda: _safe_disconnect(chan))

    def _paint(self) -> None:
        color = _BAR_RED if self._axis_error else _TRANSIT_COLORS.get(self._status, _BAR_OFF)
        self.setStyleSheet(
            f"PyDMLabel {{ color: white; background: {color};"
            f" border: 1px solid rgba(0, 0, 0, 40); border-radius: 8px; }}"
        )

    def value_changed(self, new_value) -> None:
        super().value_changed(new_value)  # renders the enum string
        try:
            self._status = int(new_value)
        except (TypeError, ValueError):
            self._status = None
        self._paint()

    def _error_changed(self, value) -> None:
        self._axis_error = bool(value)
        self._paint()


class _ErrorMessage(PyDMLabel):
    """Decoded error-message string (char waveform). Highlights red only while
    the separate error flag (``error_channel``) is set, plain otherwise."""

    def __init__(self, error_channel: str, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.setFont(_plain(10))
        self.setMinimumHeight(26)
        self.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.displayFormat = DisplayFormat.String
        self.alarmSensitiveContent = False
        self.alarmSensitiveBorder = False
        self._paint(False)

        # a second channel drives only the color, tracking the error flag
        self._error_chan = PyDMChannel(address=error_channel, value_slot=self._error_changed)
        self._error_chan.connect()
        chan = self._error_chan
        self.destroyed.connect(lambda: _safe_disconnect(chan))

    def _paint(self, error: bool) -> None:
        # read-only line-edit look (white field, thin border) so it reads as text,
        # not a button; red text/border/tint only while the error flag is set
        if error:
            colors = f"color: {_BAR_RED}; background: rgb(253, 236, 236); border: 1px solid {_BAR_RED};"
        else:
            colors = f"color: {_CELL_TXT}; background: white; border: 1px solid {_CELL_BD};"
        self.setStyleSheet(f"PyDMLabel {{ {colors} border-radius: 4px; padding: 2px 10px; }}")

    def _error_changed(self, value) -> None:
        self._paint(bool(value))


def _axis_error_channel(device: str, token: str) -> str:
    return f"ca://{device}:{token}:{_AXIS_ERROR_LEAF}"


def _safe_disconnect(chan: PyDMChannel) -> None:
    # Called from the widget's destroyed signal; the underlying connection may
    # already be gone during app teardown, so ignore that case.
    try:
        chan.disconnect()
    except Exception:
        pass


def _bool_bar(channel: str, on_color: str = _BAR_ON, off_color: str = _BAR_OFF) -> _BoolBar:
    bar = _BoolBar(on_color=on_color, off_color=off_color)
    bar.channel = channel
    return bar


def _status_bar(channel: str, error_channel: str) -> _StatusBar:
    bar = _StatusBar(error_channel)
    bar.channel = channel
    return bar


def _error_message(channel: str, error_channel: str) -> _ErrorMessage:
    lab = _ErrorMessage(error_channel)
    lab.channel = channel
    return lab


def _setpoint_combo(channel: str) -> PyDMEnumComboBox:
    combo = PyDMEnumComboBox()
    combo.setFont(_plain(10))
    combo.setMinimumHeight(28)
    combo.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
    # same look as the plain mover's target-state selector (motor_state_mover.ui)
    combo.setStyleSheet(
        "PyDMEnumComboBox { color: rgb(120, 120, 120); background-color: rgb(255, 255, 255);"
        " border: 2px solid rgb(42, 91, 215); border-radius: 3px; padding-left: 10px; }"
        "PyDMEnumComboBox::drop-down { width: 26px; border-left: 1px solid rgb(208, 208, 208); }"
        "PyDMEnumComboBox::down-arrow { image: none; border-left: 5px solid transparent;"
        " border-right: 5px solid transparent; border-top: 7px solid rgb(154, 154, 154);"
        " margin-right: 8px; }"
    )
    combo.channel = channel
    return combo


class _ExpertButton(PyDMShellCommand):
    """Icon-only shell-command button: grey cog at rest, white on the blue hover."""

    _ICON = "cog"

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.showIcon = False  # drop PyDM's default icon; we set our own
        self._rest_icon = IconFont().icon(self._ICON, QtGui.QColor(90, 90, 90))
        self._hover_icon = IconFont().icon(self._ICON, QtGui.QColor("white"))
        self.setIconSize(QtCore.QSize(16, 16))
        self._set_icon(self._rest_icon)

    def _set_icon(self, icon) -> None:
        if icon is not None:  # None when no QApplication yet
            self.setIcon(icon)

    def enterEvent(self, event) -> None:
        self._set_icon(self._hover_icon)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._set_icon(self._rest_icon)
        super().leaveEvent(event)


def _expert_button(motor: str, motor_type: str) -> _ExpertButton:
    """Opens the motor row for ``motor`` in a new window. ``motor_type`` selects
    which expert screen MotorClassicRow's own button then launches."""
    btn = _ExpertButton()
    btn.setFixedSize(34, 26)
    btn.setCursor(QtCore.Qt.PointingHandCursor)
    btn.setToolTip(f"Open the {motor_type.lower()} motor screen for {motor}")
    btn.setStyleSheet(
        f"PyDMShellCommand {{ background: rgb(233, 237, 240);"
        f" border: 1px solid {_CELL_BD}; border-radius: 4px; padding: 0; }}"
        f"PyDMShellCommand:hover {{ background: {_BAR_ON};"
        f" border: 1px solid {_BAR_ON_HOVER}; }}"
        f"PyDMShellCommand:pressed {{ background: {_BAR_ON_HOVER}; }}"
    )
    btn.commands = [f"pcdswidgets-show MotorClassicRow --motor {motor} --motor_type {motor_type}"]
    return btn


def _command_button(channel: str) -> PyDMPushButton:
    # No label -- the "Command" text was redundant; the button still writes.
    btn = PyDMPushButton()
    btn.setText("")
    btn.setMinimumHeight(26)
    btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
    btn.pressValue = "1"
    btn.setCursor(QtCore.Qt.PointingHandCursor)
    # grey at rest, blue on hover, darker blue while pressed
    btn.setStyleSheet(
        f"PyDMPushButton {{ background: rgb(233, 237, 240); border: 1px solid {_CELL_BD};"
        f" border-radius: 4px; padding: 2px 10px; }}"
        f"PyDMPushButton:hover {{ background: {_BAR_ON}; border: 1px solid {_BAR_ON_HOVER}; }}"
        f"PyDMPushButton:pressed {{ background: {_BAR_ON_HOVER}; }}"
    )
    btn.channel = channel
    return btn
