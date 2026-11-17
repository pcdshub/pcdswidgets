"""Module for EthercatTerminalStateDoubleRow"""
# Originally generated from jinja template ui_main_widget.j2
# This file can be safely edited to change the runtime behavior of the widget.

from __future__ import annotations

import functools

from pydm.widgets.channel import PyDMChannel
from qtpy import QtWidgets

from pcdswidgets.builder.designer_options import DesignerOptions
from pcdswidgets.builder.icon_options import IconOptions
from pcdswidgets.common.ethercat.ethercat_state import (
    ACCESS_GRANTED,
    access_rule,
    decode_link_text,
    decode_state_flags,
    lock_pixmap,
    set_status,
    status_stylesheet,
)
from pcdswidgets.generated.common.ethercat.ethercat_terminal_state_double_row_base import (
    EthercatTerminalStateDoubleRowBase,
)

try:
    from qtpy.QtCore import pyqtProperty
except ImportError:
    from qtpy.QtCore import Property as pyqtProperty  # type: ignore

# Channels this widget reads on top of the PyDM widgets in the .ui (key, PV suffix).
EXTRA_CHANNELS = (
    ("raw", "StateRaw"),
    ("linkcode", "LinkCode"),
    ("link", "Link_RBV"),
    ("disp", "State_SP.DISP"),
    ("disa", "State_SP.DISA"),
    ("disv", "State_SP.DISV"),
    ("sp", "State_SP"),
)


def _disconnect(channels: list):
    """Disconnect once (the list is emptied, so later calls are no-ops)."""
    while channels:
        channel = channels.pop()
        try:
            channel.disconnect()
        except Exception:
            pass


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
        self._protocol = "ca://"
        self._confirm = True
        self._values: dict = {}
        self._connected: dict = {}
        self._write_access = None
        self._channels: list[PyDMChannel] = []
        self.setStyleSheet(status_stylesheet())  # ecatStatus rules only, never the theme

        self._show_disconnected_text(self.PyDMLabel_rbv)
        combo = self.PyDMEnumComboBox_state
        # Ask before a state request is sent (the combo box would write immediately).
        combo.activated[int].disconnect(combo.internal_combo_box_activated_int)
        combo.activated[int].connect(self._on_request_activated)

        # Release the PV connections while they still exist (widget deleted or app quitting).
        self.destroyed.connect(functools.partial(_disconnect, self._channels))
        app = QtWidgets.QApplication.instance()
        if app is not None:
            app.aboutToQuit.connect(functools.partial(_disconnect, self._channels))
        self._refresh()

    # ----------------------------------------------------------- properties
    def get_confirm_requests(self) -> bool:
        """Ask for confirmation before writing State_SP (default True)."""
        return self._confirm

    def set_confirm_requests(self, value: bool) -> None:
        self._confirm = bool(value) if not isinstance(value, str) else value.strip().lower() in ("1", "true", "yes")

    confirmRequests = pyqtProperty(bool, get_confirm_requests, set_confirm_requests)

    @property
    def base(self) -> str:
        """PV base of the terminal, ``{prefix}ECAT:{port}``."""
        return f"{self.get_macro('PREFIX')}ECAT:{self.get_macro('PORT')}"

    def set_channel_protocol(self, protocol: str) -> None:
        """
        Use another PyDM data plugin for every channel, e.g. ``"loc://"`` for simulated PVs.

        Not a designer property: screens use the default ``ca://``. The terminal-states
        widget switches to ``loc://`` in mock mode.
        """
        if protocol == self._protocol:
            return
        templates = type(self)._widget_to_pre_template
        self._widget_to_pre_template = {
            widget: [
                (prop, templ.replace("ca://", protocol, 1) if isinstance(templ, str) else templ)
                for prop, templ in entries
            ]
            for widget, entries in templates.items()
        }
        self._protocol = protocol
        for macro in ("PREFIX", "PORT"):
            self._updates_for_macro(macro)
        self._reconnect()

    def after_set_macro(self, macro_name: str, value: str):
        if macro_name in ("PREFIX", "PORT"):
            self._reconnect()

    # ------------------------------------------------------------- channels
    def disconnect_channels(self):
        _disconnect(self._channels)

    def _reconnect(self):
        _disconnect(self._channels)
        self._values.clear()
        self._connected.clear()
        self._write_access = None
        if self.get_macro("PREFIX") and self.get_macro("PORT"):
            for key, suffix in EXTRA_CHANNELS:
                channel = PyDMChannel(
                    address=f"{self._protocol}{self.base}:{suffix}",
                    connection_slot=functools.partial(self._on_connection, key),
                    value_slot=functools.partial(self._on_value, key),
                    write_access_slot=self._on_write_access if key == "sp" else None,
                )
                channel.connect()
                self._channels.append(channel)
        self._refresh()

    @property
    def _mock(self) -> bool:
        return self._protocol == "loc://"

    def _on_connection(self, key, connected):
        if self._mock and not connected:
            return  # PyDM loc:// quirk: stray False right after True
        self._connected[key] = bool(connected)
        self._refresh()

    def _on_value(self, key, value):
        self._values[key] = value
        if self._mock:
            self._connected[key] = True
        self._refresh()

    def _on_write_access(self, allowed):
        self._write_access = bool(allowed)
        self._refresh()

    def _value(self, key):
        return self._values.get(key) if self._connected.get(key) else None

    # -------------------------------------------------------------- display
    def access(self) -> tuple[str, list[str]]:
        """EDITABLE / LOCKED / UNKNOWN and the lock reasons."""
        return access_rule(self._value("disp"), self._value("disa"), self._value("disv"), self._write_access)

    def _refresh(self):
        flags = decode_state_flags(self._value("raw"))
        if flags is None:
            self.flagsLabel.setText("DISCONNECTED")
            set_status(self.flagsLabel, "muted")
        else:
            self.flagsLabel.setText(" + ".join(flags) if flags else "none")
            set_status(self.flagsLabel, "fault" if flags else "")

        link = decode_link_text(self._value("linkcode"))
        if link is None and self._value("link") is not None:
            link = str(self._value("link"))  # fall back to the Link_RBV enum index text
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
        why = "\n".join(reasons) if reasons else ACCESS_GRANTED
        for widget in (self.accessIcon, self.accessLabel):
            widget.setToolTip(f"{access}\n{why}")
        self.requestFrame.setEnabled(access == "EDITABLE")
        self.requestFrame.setToolTip("" if access == "EDITABLE" else f"Requests disabled: {access}\n{why}")

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
    def _on_request_activated(self, index: int):
        combo = self.PyDMEnumComboBox_state
        target = combo.itemText(index)
        current = combo.value
        if current is not None and int(current) == index:
            return  # same as the last request: nothing to send
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
                if current is not None:
                    combo.setCurrentIndex(int(current))  # revert the selection
                return
        combo.internal_combo_box_activated_int(index)
