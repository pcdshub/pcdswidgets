"""
Expanded motor state mover (variant 2).

A self-contained replacement for the Typhos expert screen (no Typhos dependency):
the plain :class:`MotorStateMover` on top (with its own Expert Screen button
hidden -- we are already in the expert screen), then a tab group with

* **Normal** -- always present: the raw device signals (busy, done, error,
  error_id, error_message, reset_cmd), matching the plain state-mover expert
  screen.
* **Configuration** -- shown *only* when the caller provides both ``stateCount``
  and ``motorTokens`` (the plain expert screen has no config tab; the configured
  one does). A read-only per-state config grid whose size is driven by two
  properties instead of a fixed .ui:

  - ``stateCount`` -- number of states (grid rows).
  - ``motorTokens`` -- comma-separated per-motor tokens (grid motor-columns). The
    tokens are device specific (e.g. ``D1M1,D3M1``) and cannot be generated from a
    count, so they are listed explicitly. ``motor_count`` == number of tokens.

Everything here is read-only display (plus the reset command). Config cells
resolve to::

    ca://{motor}:STATE:{token}:{NN}:{leaf}_RBV

with ``{NN}`` the zero-padded 2-digit state index and ``{leaf}`` one of
``NAME``, ``SETPOINT``, ``VELO``, ``MOVE_OK``.
"""

from __future__ import annotations

from pydm.widgets.byte import PyDMByteIndicator
from pydm.widgets.display_format import DisplayFormat
from pydm.widgets.label import PyDMLabel
from pydm.widgets.pushbutton import PyDMPushButton
from qtpy import QtCore, QtGui, QtWidgets

from pcdswidgets.builder.designer_options import DesignerOptions
from pcdswidgets.builder.icon_options import IconOptions
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
# state mover's moving LED)
_BAR_ON = "rgb(20, 100, 239)"
_BAR_OFF = "rgb(150, 150, 150)"

# "Normal" tab device signals: (row label, PV suffix under ${MOTOR}, kind).
# kind: "led" -> boolean rendered as an LED indicator; "text" -> numeric text;
#       "string" -> char waveform decoded and shown as a string.
_NORMAL_SIGNALS = (
    ("busy", "STATE:BUSY_RBV", "led"),
    ("done", "STATE:DONE_RBV", "led"),
    ("error", "STATE:ERR_RBV", "led"),
    ("error_id", "STATE:ERRID_RBV", "text"),
    ("error_message", "STATE:ERRMSG_RBV", "string"),
)
_RESET_SUFFIX = "STATE:RESET"

_TAB_STYLE = (
    "QTabWidget::pane { border: 1px solid rgb(207, 214, 220); border-radius: 6px;"
    " top: -1px; background: rgb(251, 252, 253); }"
    "QTabBar::tab { background: rgb(233, 237, 240); color: rgb(125, 125, 125);"
    " padding: 6px 18px; border: 1px solid rgb(207, 214, 220); border-bottom: none;"
    " border-top-left-radius: 6px; border-top-right-radius: 6px; margin-right: 2px; }"
    f"QTabBar::tab:selected {{ background: rgb(251, 252, 253); color: {_SLATE}; }}"
)


class MotorStateMoverExpanded(QtWidgets.QFrame):
    """Plain state mover + a read-only, dynamically sized state-config grid."""

    designer_options = DesignerOptions(
        group="ECS Motion Common",
        is_container=False,
        icon=IconOptions.NONE,
    )
    _qt_designer_ = {
        "group": designer_options.group,
        "is_container": designer_options.is_container,
    }

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self._motor = ""
        self._state_count = 0
        self._state_start = 1
        self._motor_tokens = ""

        self._outer = QtWidgets.QVBoxLayout(self)
        self._outer.setContentsMargins(8, 8, 8, 8)
        self._outer.setSpacing(8)

        # plain state mover on top, always visible (reused verbatim, minus its
        # own Expert Screen button -- we are already inside the expert screen)
        self.plainMover = MotorStateMover(self)
        expert_btn = getattr(self.plainMover, "expertScreenButton", None)
        if expert_btn is not None:
            expert_btn.hide()
        self._outer.addWidget(self.plainMover)

        self.tabs = QtWidgets.QTabWidget(self)
        self.tabs.setStyleSheet(_TAB_STYLE)

        # "Normal" tab: always present -- the raw device signals
        self._normal_tab = QtWidgets.QWidget()
        self._normal_layout = QtWidgets.QVBoxLayout(self._normal_tab)
        self._normal_layout.setContentsMargins(14, 14, 14, 14)
        self.tabs.addTab(self._normal_tab, "Normal")

        # "Configuration" tab: built here but attached only when state_count and
        # motor tokens are provided by the caller (see _sync_config_tab)
        self._config_tab = QtWidgets.QWidget()
        self._config_layout = QtWidgets.QVBoxLayout(self._config_tab)
        self._config_layout.setContentsMargins(12, 12, 12, 12)

        self._outer.addWidget(self.tabs)
        self._rebuild_normal()
        self._rebuild_grid()

    # ------------------------------------------------------------------ props
    def get_motor(self) -> str:
        return self._motor

    def set_motor(self, value: str) -> None:
        self._motor = value
        self.plainMover.setProperty("motor", value)
        self._rebuild_normal()
        self._rebuild_grid()

    motor = pyqtProperty(str, get_motor, set_motor)

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

    def get_motor_tokens(self) -> str:
        return self._motor_tokens

    def set_motor_tokens(self, value: str) -> None:
        self._motor_tokens = value
        self._rebuild_grid()

    motorTokens = pyqtProperty(str, get_motor_tokens, set_motor_tokens)

    # ------------------------------------------------------------------ build
    @property
    def _tokens(self) -> list[str]:
        return [t.strip() for t in self._motor_tokens.split(",") if t.strip()]

    def _channel(self, token: str, index: int, leaf: str) -> str:
        return f"ca://{self._motor}:STATE:{token}:{index:02d}:{leaf}_RBV"

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

        row = 0
        for label, suffix, kind in _NORMAL_SIGNALS:
            form.addWidget(_row_label(label), row, 0)
            channel = f"ca://{self._motor}:{suffix}"
            if kind == "led":
                form.addWidget(_bool_bar(channel), row, 1)
            else:
                form.addWidget(_signal_value(channel, as_string=kind == "string"), row, 1)
            row += 1

        # reset_cmd: just the Command push button (the LED was redundant)
        form.addWidget(_row_label("reset_cmd"), row, 0)
        form.addWidget(_command_button(f"ca://{self._motor}:{_RESET_SUFFIX}"), row, 1)

        self._normal_layout.addWidget(panel)
        self._normal_layout.addStretch(1)

    def _config_provided(self) -> bool:
        """The Configuration tab only exists when the caller supplies both."""
        return self._state_count > 0 and bool(self._tokens)

    def _sync_config_tab(self) -> None:
        idx = self.tabs.indexOf(self._config_tab)
        if self._config_provided():
            if idx == -1:
                self.tabs.addTab(self._config_tab, "Configuration")
        elif idx != -1:
            self.tabs.removeTab(idx)  # detach (does not delete the widget)

    def _rebuild_grid(self) -> None:
        self._clear_layout(self._config_layout)
        if not self._config_provided():
            self._sync_config_tab()
            return

        tokens = self._tokens
        box = QtWidgets.QWidget()
        grid = QtWidgets.QGridLayout(box)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(5)

        # header rows: State | Motor k (Setpoint, Velo, Move OK) x N
        grid.addWidget(_hdr("State"), 0, 0, 2, 1)
        col = 1
        for m, _token in enumerate(tokens):
            grid.addWidget(_hdr(f"Motor {m + 1}"), 0, col, 1, 3)
            grid.addWidget(_hdr("Setpoint", sub=True), 1, col)
            grid.addWidget(_hdr("Velo", sub=True), 1, col + 1)
            grid.addWidget(_hdr("Move OK", sub=True), 1, col + 2)
            col += 3

        for r in range(self._state_count):
            index = self._state_start + r
            row = r + 2
            # state name: read from the first motor token
            name = _cell_label(self._channel(tokens[0], index, "NAME"), bold=True, align=QtCore.Qt.AlignLeft)
            grid.addWidget(name, row, 0)

            col = 1
            for token in tokens:
                grid.addWidget(_cell_label(self._channel(token, index, "SETPOINT")), row, col)
                grid.addWidget(_cell_label(self._channel(token, index, "VELO")), row, col + 1)
                grid.addWidget(_move_ok(self._channel(token, index, "MOVE_OK")), row, col + 2, QtCore.Qt.AlignCenter)
                col += 3

        self._config_layout.addWidget(box)
        self._config_layout.addStretch(1)
        self._sync_config_tab()


# --------------------------------------------------------------------- helpers
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


def _cell_label(channel: str, bold: bool = False, align=QtCore.Qt.AlignCenter) -> PyDMLabel:
    lab = PyDMLabel()
    lab.setFont(_bold(10) if bold else _plain(10))
    lab.setFixedHeight(28)
    lab.setMinimumWidth(80)
    lab.setAlignment(align)
    lab.showUnits = True
    lab.setStyleSheet(
        f"PyDMLabel {{ color: {_CELL_TXT}; background: {_CELL_BG};"
        f" border: 1px solid {_CELL_BD}; border-radius: 4px; padding: 0 8px; }}"
    )
    lab.channel = channel
    return lab


def _move_ok(channel: str) -> PyDMByteIndicator:
    ind = PyDMByteIndicator()
    ind.setFixedSize(18, 18)
    ind.numBits = 1
    ind.circles = True
    ind.showLabels = False
    ind.alarmSensitiveContent = False
    ind.alarmSensitiveBorder = False
    ind.onColor = QtGui.QColor(0, 192, 0)
    ind.offColor = QtGui.QColor(183, 183, 183)
    ind.channel = channel
    return ind


def _row_label(text: str) -> QtWidgets.QLabel:
    lab = QtWidgets.QLabel(text)
    lab.setFont(_bold(10))
    lab.setMinimumWidth(100)
    lab.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
    lab.setStyleSheet(f"color: {_SLATE}; background: transparent;")
    return lab


def _signal_value(channel: str, as_string: bool = False) -> PyDMLabel:
    lab = PyDMLabel()
    lab.setFont(_plain(10))
    lab.setMinimumHeight(26)
    lab.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
    lab.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
    if as_string:
        # ERRMSG_RBV is a char waveform; decode it to a string instead of
        # showing the raw array of character codes.
        lab.displayFormat = DisplayFormat.String
    lab.setStyleSheet(
        f"PyDMLabel {{ color: {_CELL_TXT}; background: {_CELL_BG};"
        f" border: 1px solid {_CELL_BD}; border-radius: 4px; padding: 2px 10px; }}"
    )
    lab.channel = channel
    return lab


class _BoolBar(PyDMLabel):
    """Full-width rounded bar (Typhos-style): blue when the value is set, grey
    when clear, with the value shown as text."""

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.setFont(_bold(10))
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setMinimumHeight(26)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.alarmSensitiveContent = False
        self.alarmSensitiveBorder = False
        self._paint(False)

    def _paint(self, on: bool) -> None:
        self.setStyleSheet(
            f"PyDMLabel {{ color: white; background: {_BAR_ON if on else _BAR_OFF};"
            f" border: 1px solid rgba(0, 0, 0, 40); border-radius: 8px; }}"
        )

    def value_changed(self, new_value) -> None:
        super().value_changed(new_value)  # renders the value text
        self._paint(bool(new_value))


def _bool_bar(channel: str) -> _BoolBar:
    bar = _BoolBar()
    bar.channel = channel
    return bar


def _command_button(channel: str) -> PyDMPushButton:
    btn = PyDMPushButton()
    btn.setText("Command")
    btn.setFont(_bold(10))
    btn.setMinimumHeight(26)
    btn.pressValue = "1"
    btn.setStyleSheet(
        "color: rgb(20, 20, 20); background: rgb(245, 245, 245);"
        " border: 1px solid rgb(219, 219, 219); border-radius: 4px; padding: 2px 10px;"
    )
    btn.channel = channel
    return btn
