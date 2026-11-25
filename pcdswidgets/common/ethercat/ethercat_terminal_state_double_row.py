"""Module for EthercatTerminalStateDoubleRow"""
# Originally generated from jinja template ui_main_widget.j2
# This file can be safely edited to change the runtime behavior of the widget.

from __future__ import annotations

import functools

from qtpy import QtWidgets

from pcdswidgets.builder.designer_options import DesignerOptions
from pcdswidgets.builder.icon_options import IconOptions
from pcdswidgets.common.ethercat.constants import to_bool
from pcdswidgets.common.ethercat.model import Terminal, access_rule, access_tooltip
from pcdswidgets.common.ethercat.monitor import TerminalMonitor, release_monitors, session_read_only
from pcdswidgets.common.ethercat.style import lock_pixmap, set_status, status_stylesheet
from pcdswidgets.generated.common.ethercat.ethercat_terminal_state_double_row_base import (
    EthercatTerminalStateDoubleRowBase,
)

try:
    from qtpy.QtCore import pyqtProperty
except ImportError:
    from qtpy.QtCore import Property as pyqtProperty  # type: ignore


class EthercatTerminalStateDoubleRow(EthercatTerminalStateDoubleRowBase):
    """
    One EtherCAT terminal: state, state flags, decoded link, access, and a state request.

    Set ``prefix`` (IOC prefix incl. trailing colon, e.g. ``PLC:ICL:IOC:``) and
    ``port`` (EtherCAT fixed address, e.g. ``1015``); ``terminal_name`` and
    ``terminal_type`` only label the widget. PVs are ``{prefix}ECAT:{port}:...``.

    The Request combo box is enabled only when the terminal is EDITABLE
    (``State_SP.DISP == 0`` and ``DISA != DISV`` and Channel Access write access);
    the lock reasons are in the Access tooltip. A request asks for confirmation
    first unless ``confirmRequests`` is off.
    """

    designer_options = DesignerOptions(
        group="ECS Common Ethercat",
        is_container=False,
        icon=IconOptions.NONE,
    )

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self._confirm = True
        self._monitor: TerminalMonitor | None = None  # the monitor shown (own or shared)
        self._adopting = False  # set_monitor() is setting the macros: do not reconnect
        # The monitor this widget created (0 or 1), released on reconnect / deletion. A list,
        # so the destroyed / aboutToQuit handlers never touch this (possibly deleted) widget.
        self._owned: list[TerminalMonitor] = []
        self.setStyleSheet(status_stylesheet())  # ecatStatus rules only, never the theme

        self._show_disconnected_text(self.PyDMLabel_rbv)
        # The Request combo box (a ConfirmingEnumComboBox) writes only what this accepts.
        self.PyDMEnumComboBox_state.confirm = self._confirm_request

        # Release the PV connections while they still exist (widget deleted or app quitting).
        self.destroyed.connect(functools.partial(release_monitors, self._owned))
        app = QtWidgets.QApplication.instance()
        if app is not None:
            app.aboutToQuit.connect(functools.partial(release_monitors, self._owned))
        self._repaint_status()

    # ----------------------------------------------------------- properties
    def get_confirm_requests(self) -> bool:
        """Ask for confirmation before writing State_SP (default True)."""
        return self._confirm

    def set_confirm_requests(self, value: bool) -> None:
        self._confirm = to_bool(value)

    confirmRequests = pyqtProperty(bool, get_confirm_requests, set_confirm_requests)

    @property
    def base(self) -> str:
        """PV base of the terminal, ``{prefix}ECAT:{port}``."""
        return f"{self.get_macro('PREFIX')}ECAT:{self.get_macro('PORT')}"

    def after_set_macro(self, macro_name: str, value: str):
        if macro_name in ("PREFIX", "PORT") and not self._adopting:
            self._reconnect()

    # ------------------------------------------------------------- channels
    @property
    def monitor(self) -> TerminalMonitor | None:
        """The terminal's PV subscription, ``None`` until ``prefix`` and a numeric ``port`` are set."""
        return self._monitor

    def set_monitor(self, monitor: TerminalMonitor, prefix: str) -> None:
        """
        Show a terminal through an existing (shared) :class:`TerminalMonitor`.

        Used by :class:`EthercatTerminalStatesStretch`, which already monitors every
        terminal: no second subscription is made and the PV macros are set once. The
        monitor stays owned by the caller; this widget never disconnects it.
        """
        self._set_shown(monitor)
        terminal = monitor.terminal
        self._adopting = True
        try:
            self.setProperty("terminal_name", terminal.display_name)
            self.setProperty("terminal_type", terminal.type)
            self.setProperty("prefix", prefix)
            self.setProperty("port", str(terminal.port))
        finally:
            self._adopting = False
        self._repaint_status()

    def disconnect_channels(self):
        """Release this widget's own subscription and stop showing a shared one."""
        self._set_shown(None)

    def _set_shown(self, monitor: TerminalMonitor | None):
        """Show ``monitor``: drop the previous one (released only if this widget owns it)."""
        previous = self._monitor
        if previous is not None and previous is not monitor:
            try:
                previous.changed.disconnect(self._repaint_status)
            except (RuntimeError, TypeError):
                pass  # already deleted or disconnected
        if monitor is None or monitor not in self._owned:
            release_monitors(self._owned)
        self._monitor = monitor
        if monitor is not None and monitor is not previous:
            monitor.changed.connect(self._repaint_status)

    def _reconnect(self):
        prefix, port = self.get_macro("PREFIX"), self.get_macro("PORT")
        shown = self._monitor
        if shown is not None and shown.base == self.base:
            self._repaint_status()  # already showing this terminal
            return
        self._set_shown(None)
        if prefix and port and str(port).strip().isdigit():
            monitor = TerminalMonitor(Terminal(port, name="", type=""), prefix)  # labels come from the macros
            self._owned.append(monitor)
            self._set_shown(monitor)
            monitor.connect_channels()
        self._repaint_status()

    # -------------------------------------------------------------- display
    def access(self) -> tuple[str, list[str]]:
        """EDITABLE / LOCKED / UNKNOWN and the lock reasons."""
        monitor = self.monitor
        return monitor.access if monitor is not None else access_rule(None, None, None)

    def _repaint_status(self):
        """Repaint the labels from the monitor's latest PV values (on each of its ``changed``)."""
        monitor = self.monitor
        flags = monitor.state_flags if monitor is not None else None
        if flags is None:
            self.flagsLabel.setText("DISCONNECTED")
            set_status(self.flagsLabel, "muted")
        else:
            self.flagsLabel.setText(" + ".join(flags) if flags else "none")
            set_status(self.flagsLabel, "fault" if flags else "")

        link = (monitor.link_detail or monitor.link_text) if monitor is not None else None
        if link is None:
            self.linkLabel.setText("DISCONNECTED")
            set_status(self.linkLabel, "muted")
        else:
            self.linkLabel.setText(link)
            set_status(self.linkLabel, "" if link == "OK" else "fault")
        self.linkLabel.setToolTip(f"{link or 'DISCONNECTED'}\n{self.base}:LinkCode / Link_RBV")

        access, reasons = self.access()
        size = max(12, int(self.accessLabel.fontMetrics().height() * 0.8))
        self.accessIcon.setPixmap(lock_pixmap(access, size))
        self.accessLabel.setText(access)
        set_status(self.accessLabel, {"EDITABLE": "editable", "LOCKED": ""}.get(access, "muted"))
        tip = access_tooltip(access, reasons, session_read_only())
        for widget in (self.accessIcon, self.accessLabel):
            widget.setToolTip(tip)
        can_request, _ = self._can_request()
        self.requestFrame.setEnabled(can_request)
        self.requestFrame.setToolTip("" if can_request else f"Requests disabled: {tip}")

    @staticmethod
    def _show_disconnected_text(label):
        """A disconnected PyDMLabel shows its PV address; show DISCONNECTED instead."""
        if "disconnectedText" in dir(type(label)):  # pydm >= 1.28
            label.setProperty("disconnectedText", "DISCONNECTED")
            label.check_enable_state()
            return
        original = label.check_enable_state

        def check_enable_state():
            original()
            if not label._connected:
                label.setText("DISCONNECTED")

        label.check_enable_state = check_enable_state
        check_enable_state()

    # -------------------------------------------------------------- request
    def _can_request(self) -> tuple[bool, str]:
        """Whether State_SP may be written now, and the access tooltip."""
        access, reasons = self.access()
        read_only = session_read_only()
        return access == "EDITABLE" and not read_only, access_tooltip(access, reasons, read_only)

    def _confirm_request(self, index: int) -> bool:
        """
        The Request combo box's ``confirm`` hook: True writes State_SP, False puts the
        selection back. Asks the user first (unless ``confirmRequests`` is off) and checks
        access again right before writing, since PV updates keep arriving during the dialog.
        """
        combo = self.PyDMEnumComboBox_state
        target = combo.itemText(index)
        if combo.value is not None and int(combo.value) == index:
            return False  # same as the last request: nothing to send
        if self._confirm:
            name = self.get_macro("TERMINAL_NAME") or self.base
            answer = QtWidgets.QMessageBox.question(
                self,
                "Request EtherCAT state",
                f"Request EtherCAT state {target} for {name} (port {self.get_macro('PORT')})?\n\n{self.base}:State_SP",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No,
            )
            if answer != QtWidgets.QMessageBox.Yes:
                return False
        allowed, why = self._can_request()
        if not allowed:
            QtWidgets.QMessageBox.warning(
                self, "Request not sent", f"State {target} was not requested for {self.base}:\n\n{why}"
            )
        return allowed
