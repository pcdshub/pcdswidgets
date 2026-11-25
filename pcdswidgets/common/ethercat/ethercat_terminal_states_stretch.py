"""Module for EthercatTerminalStatesStretch"""
# Originally generated from jinja template ui_main_widget.j2
# This file can be safely edited to change the runtime behavior of the widget.

from __future__ import annotations

import functools
import sys
from datetime import datetime
from pathlib import Path

from qtpy import QtCore, QtGui, QtWidgets
from qtpy.QtCore import Qt

from pcdswidgets.builder.designer_options import DesignerOptions
from pcdswidgets.builder.icon_options import IconOptions
from pcdswidgets.common.ethercat import discover
from pcdswidgets.common.ethercat.constants import LINK_ENUM, STATE_ENUM, to_bool
from pcdswidgets.common.ethercat.ethercat_state import (
    FAULT_RED,
    GOOD_LINK,
    GOOD_STATE,
    H_DISCONNECTED,
    H_OK,
    HEALTHS,
    LOCK_COLORS,
    MUTED_GREY,
    Node,
    TerminalMonitor,
    access_tooltip,
    build_tree,
    dot_pixmap,
    load_discovery,
    lock_pixmap,
    release_monitors,
    status_stylesheet,
)
from pcdswidgets.generated.common.ethercat.ethercat_terminal_states_stretch_base import (
    EthercatTerminalStatesStretchBase,
)

try:
    from qtpy.QtCore import pyqtProperty
except ImportError:
    from qtpy.QtCore import Property as pyqtProperty  # type: ignore

COL_NAME, COL_PORT, COL_STATE, COL_LINK, COL_ACCESS = range(5)
ROLE_PORT = Qt.UserRole + 1
SHOW_ALL, SHOW_FAULTS, SHOW_NOT_OP, SHOW_LINK, SHOW_EDITABLE, SHOW_DISCONNECTED = range(6)


def _set_foreground(item, col, color):
    """Tree text colour; None clears it so the theme's text colour applies."""
    item.setData(col, Qt.ForegroundRole, QtGui.QBrush(color) if color is not None else None)


def _expand_parents(item):
    """Expand every ancestor of a tree item so it is visible."""
    parent = item.parent()
    while parent is not None:
        parent.setExpanded(True)
        parent = parent.parent()


class EthercatTerminalStatesStretch(EthercatTerminalStatesStretchBase):
    """
    Every EtherCAT terminal of one PLC as a tree, with status roll-up and a state panel.

    Designer properties: ``plc`` (host used for discovery, e.g. ``plc-sds-raptor``),
    ``prefix`` (IOC prefix incl. trailing colon, e.g. ``PLC:ICL:IOC:``),
    ``discoveryFile`` (read-only discovery JSON, default ``~/.cache/ecat-states/<plc>.json``)
    and ``confirmRequests``. The discovery is refreshed with the Rediscover button
    (``ads read-ecat-topology``, needs ads-actions; the EtherCAT master's AMS Net ID is
    resolved by ads-actions).

    Every group / Port row and every junction terminal shows the worst status below
    it (grey dot = OK, red = not OP / link not OK / state flag, dashed ring =
    disconnected). Selecting a terminal shows an :class:`EthercatTerminalStateDoubleRow`.
    """

    designer_options = DesignerOptions(
        group="ECS Common Ethercat",
        is_container=False,
        icon=IconOptions.NONE,
    )

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self._plc = ""
        self._prefix = ""
        self._discovery_file = ""
        self._confirm = True

        self.monitors: dict[int, TerminalMonitor] = {}
        self.terminal_items: dict[int, QtWidgets.QTreeWidgetItem] = {}
        self.meta: dict = {}
        self._process: QtCore.QProcess | None = None
        self._refresh_timer = QtCore.QTimer(self, singleShot=True, interval=150)
        self._refresh_timer.timeout.connect(self.refresh)
        # Properties can arrive in any order (designer, .ui, code): reload once they settle.
        self._reload_timer = QtCore.QTimer(self, singleShot=True, interval=0)
        self._reload_timer.timeout.connect(self.reload)

        self.setStyleSheet(status_stylesheet())  # ecatStatus rules only, never the theme
        self._setup_widgets()
        # Release the PV connections even when the widget is deleted without a closeEvent
        # (embedded in a screen that goes away). ``self.monitors`` is never rebound.
        self.destroyed.connect(functools.partial(release_monitors, self.monitors))
        app = QtWidgets.QApplication.instance()
        if app is not None:
            app.aboutToQuit.connect(functools.partial(release_monitors, self.monitors))
        self.reload()

    # ----------------------------------------------------------- properties
    def _prop_changed(self):
        self._reload_timer.start()

    def get_plc(self) -> str:
        """PLC host name used for discovery, e.g. plc-sds-raptor."""
        return self._plc

    def set_plc(self, value: str) -> None:
        if value != self._plc:
            self._plc = str(value).strip()
            self._prop_changed()

    plc = pyqtProperty(str, get_plc, set_plc)

    def get_prefix(self) -> str:
        """IOC PV prefix including the trailing colon, e.g. PLC:ICL:IOC:."""
        return self._prefix

    def set_prefix(self, value: str) -> None:
        if value != self._prefix:
            self._prefix = str(value).strip()
            self._prop_changed()

    prefix = pyqtProperty(str, get_prefix, set_prefix)

    def get_discovery_file(self) -> str:
        """Discovery JSON or a directory for <dir>/<plc>.json (default ~/.cache/ecat-states); written by Rediscover."""
        return self._discovery_file

    def set_discovery_file(self, value: str) -> None:
        if value != self._discovery_file:
            self._discovery_file = str(value).strip()
            self._prop_changed()

    discoveryFile = pyqtProperty(str, get_discovery_file, set_discovery_file)

    def get_confirm_requests(self) -> bool:
        """Ask for confirmation before writing State_SP (default True)."""
        return self._confirm

    def set_confirm_requests(self, value: bool) -> None:
        self._confirm = to_bool(value)
        self.terminalWidget.setProperty("confirmRequests", self._confirm)

    confirmRequests = pyqtProperty(bool, get_confirm_requests, set_confirm_requests)

    # ---------------------------------------------------------------- set up
    def _setup_widgets(self):
        tree = self.terminalTree
        header = tree.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(COL_NAME, QtWidgets.QHeaderView.Stretch)
        for col in (COL_PORT, COL_STATE, COL_LINK, COL_ACCESS):
            header.setSectionResizeMode(col, QtWidgets.QHeaderView.Fixed)
        header.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        tree.installEventFilter(self)
        tree.currentItemChanged.connect(self._on_current_item_changed)

        self.showCombo.currentIndexChanged.connect(self._on_filter_changed)
        self.filterEdit.textChanged.connect(self._on_filter_changed)
        self.expandButton.clicked.connect(tree.expandAll)
        self.collapseButton.clicked.connect(lambda: tree.collapseAll())
        self.rediscoverButton.clicked.connect(self.rediscover)
        self._make_icons()
        self._update_column_widths()

    def eventFilter(self, obj, event):
        if obj is self.terminalTree and event.type() == QtCore.QEvent.FontChange:
            self._make_icons()
            self._update_column_widths()
            self._schedule_refresh()
        return super().eventFilter(obj, event)

    def _make_icons(self):
        size = max(10, int(self.terminalTree.fontMetrics().height() * 0.7))
        self.terminalTree.setIconSize(QtCore.QSize(size, size))
        self._dots = {h: QtGui.QIcon(dot_pixmap(h, size)) for h in HEALTHS}
        self._locks = {access: QtGui.QIcon(lock_pixmap(access, size)) for access in LOCK_COLORS}

    def _update_column_widths(self):
        """Fixed columns sized from the enum strings so zooming never clips them."""
        tree = self.terminalTree
        metrics = QtGui.QFontMetrics(tree.font())
        header_metrics = QtGui.QFontMetrics(tree.header().font())

        def width(strings, header_text):
            text_w = max(metrics.horizontalAdvance(s) for s in strings)
            return max(text_w, header_metrics.horizontalAdvance(header_text)) + 12

        ports = [str(port) for port in self.monitors] or ["0000"]
        tree.setColumnWidth(COL_PORT, width(ports, "Port"))
        tree.setColumnWidth(COL_STATE, width(STATE_ENUM + ("UNKNOWN", "DISCONNECTED", "ALL OP", "88 NOT OP"), "State"))
        tree.setColumnWidth(COL_LINK, width(LINK_ENUM + ("DISCONNECTED", "ALL OK", "88 NOT OK"), "Link"))
        header_item = tree.headerItem()
        header_item.setText(COL_ACCESS, "")
        header_item.setIcon(COL_ACCESS, self._locks["LOCKED"])
        header_item.setToolTip(
            COL_ACCESS, "Access: open lock = EDITABLE (State_SP.DISP == 0 and DISA != DISV), closed lock = LOCKED"
        )
        tree.setColumnWidth(COL_ACCESS, tree.iconSize().width() + 22)

    # -------------------------------------------------------------- discovery
    def _title(self) -> str:
        return f"EtherCAT Terminal States - {self._plc or 'set the plc property'}"

    def _default_discovery(self) -> Path:
        return discover.resolve_output(None, self._plc or "unknown")

    def discovery_target(self) -> Path:
        """
        Where the discovery file is read from and written to.

        ``discoveryFile`` may be a file or a directory (then ``<dir>/<plc>.json``);
        empty means ``~/.cache/ecat-states/<plc>.json``.
        """
        return discover.resolve_output(self._discovery_file or None, self._plc or "unknown")

    def _write_target(self) -> Path:
        """The discovery target, or the user cache if the target location is not writable."""
        target = self.discovery_target()
        return target if discover.can_create(target) else self._default_discovery()

    def reload(self):
        """(Re)load the discovery file and (re)connect every terminal. Never runs a discovery itself."""
        self._reload_timer.stop()
        self.DeviceName.setText(self._title())
        ads = discover.find_ads()
        self.rediscoverButton.setEnabled(bool(self._plc) and ads is not None and self._process is None)
        if ads is None:
            self.rediscoverButton.setToolTip(
                "ads-actions not found: run `ctrlenv-pathmunge ads-actions` before launching"
            )
        if not self._plc and not self._discovery_file:
            self._show_message("Set the plc and prefix properties (and optionally discoveryFile).")
            return
        target = self.discovery_target()
        candidates = [p for p in {target, self._write_target()} if p.is_file()]
        if not candidates:
            self._explain_missing(target, ads)
            return
        newest = max(candidates, key=lambda f: f.stat().st_mtime)
        try:
            self.meta, terminals = load_discovery(newest)
        except Exception as ex:
            self._show_message(f"Could not read {newest}: {ex}")
            return
        self.meta["_path"] = str(newest)
        self._build(terminals)

    def _explain_missing(self, target: Path, ads: str | None):
        """No discovery file yet: say how to create one. Discovery only ever runs when the user asks."""
        output = self._write_target()
        where = str(output) + ("" if output == target else f" ({target.parent} is not writable)")
        cli = f"python -m pcdswidgets.common.ethercat.discover {self._plc or '<plc>'} -o {target}"
        if self._process is not None:
            self._show_message(f"Creating {where} (read-only discovery)...")
        elif not self._plc:
            self._show_message(f"No discovery file at {target}. Set the plc property to discover the terminals.")
        elif ads is None:
            self._show_message(
                f"No discovery file at {target}. Load ads-actions (ctrlenv-pathmunge ads-actions) "
                f"and press Rediscover, or run: {cli}"
            )
        else:
            self._show_message(f"No discovery file at {target}. Press Rediscover to create {where}, or run: {cli}")

    @QtCore.Slot()  # clicked(bool) calls it without arguments; a bound method, never a lambda over self
    def rediscover(self):
        """Run the read-only discovery (ads read-ecat-topology) in the background. User action only."""
        if self._process is not None or not self._plc:
            return
        output = self._write_target()
        args = ["-m", "pcdswidgets.common.ethercat.discover", self._plc, "-o", str(output)]
        process = QtCore.QProcess(self)
        process.setProcessChannelMode(QtCore.QProcess.MergedChannels)
        process.finished.connect(lambda code, _status: self._on_discovery_done(code, output))
        self._process = process
        self.rediscoverButton.setEnabled(False)
        self.rediscoverButton.setText("Discovering...")
        if not self.monitors:  # nothing loaded yet: show progress in the tree
            self._show_message(f"Creating {output} (read-only discovery)...")
        process.start(sys.executable, args)

    def _on_discovery_done(self, code: int, output: Path):
        log = bytes(self._process.readAll()).decode(errors="replace").strip()
        self._process.deleteLater()
        self._process = None
        self.rediscoverButton.setEnabled(True)
        self.rediscoverButton.setText("Rediscover")
        if code == 0 and output.is_file():
            self.reload()
            return
        detail = "\n".join(log.splitlines()[-6:]) if log else f"exit code {code}"
        if not self.monitors:  # still nothing loaded: restore the explanation in the tree
            self.reload()
        QtWidgets.QMessageBox.warning(
            self, "Discovery failed", f"Read-only discovery of {self._plc} failed:\n\n{detail}"
        )

    def _show_message(self, text: str):
        self.teardown()
        self.terminalTree.clear()
        item = QtWidgets.QTreeWidgetItem([text])
        _set_foreground(item, COL_NAME, MUTED_GREY)
        self.terminalTree.addTopLevelItem(item)
        self.refresh()

    # ------------------------------------------------------------------- build
    def _build(self, terminals):
        self.teardown()
        tree = self.terminalTree
        tree.clear()
        for t in terminals:
            monitor = TerminalMonitor(t, self._prefix, self)
            monitor.changed.connect(self._schedule_refresh)
            self.monitors[t.port] = monitor

        for node in build_tree(terminals):
            tree.addTopLevelItem(self._make_item(node))
        tree.collapseAll()  # default: top-level groups only (each carries its status)
        self._update_column_widths()

        generated = self.meta.get("generated", "")
        try:
            generated = datetime.fromisoformat(generated).strftime("%Y-%m-%d %H:%M")
        except (TypeError, ValueError):
            pass
        sources = " + ".join(s.split()[1] for s in self.meta.get("sources", []) if " " in s)
        info = (
            f"{self.meta.get('plc', self._plc)}: {len(terminals)} terminals, discovered "
            f"{generated} ({sources or 'ads-actions'})\n{self.meta.get('_path', '')}\n"
            f"PVs {self._prefix}ECAT:<port>:State_RBV / Link_RBV / State_SP"
        )
        self.DeviceName.setToolTip(info)
        self.rediscoverButton.setToolTip(
            "Re-run the read-only ads-actions discovery (read-ecat-topology)\n\nLast discovery: " + info
        )
        for monitor in self.monitors.values():
            monitor.connect_channels()
        self.refresh()

    def _make_item(self, node: Node) -> QtWidgets.QTreeWidgetItem:
        item = QtWidgets.QTreeWidgetItem()
        if node.kind == "terminal":
            t = node.terminal
            item.setText(COL_NAME, t.name)
            item.setData(COL_NAME, ROLE_PORT, t.port)
            item.setText(COL_PORT, str(t.port))
            self.terminal_items[t.port] = item
        else:
            count = node.count_terminals()
            item.setText(COL_NAME, f"{node.label} ({count})")
            item.setToolTip(COL_NAME, f"{node.tooltip}\n{count} terminal{'s' if count != 1 else ''}")
        for child in node.children:
            item.addChild(self._make_item(child))
        return item

    def teardown(self):
        """Disconnect every PV (the terminal panel first: it shares the monitors' connections)."""
        try:
            self.terminalWidget.disconnect_channels()
        except RuntimeError:  # already deleted
            pass
        monitors = list(self.monitors.values())
        release_monitors(self.monitors)
        for monitor in monitors:
            monitor.deleteLater()
        self.terminal_items.clear()
        self._show_detail(None)

    def closeEvent(self, event):
        self.teardown()
        super().closeEvent(event)

    # ----------------------------------------------------------------- refresh
    def _schedule_refresh(self):
        if not self._refresh_timer.isActive():
            self._refresh_timer.start()

    def refresh(self):
        tree = self.terminalTree
        bold = QtGui.QFont(tree.font())
        bold.setBold(True)
        for index in range(tree.topLevelItemCount()):
            self._refresh_item(tree.topLevelItem(index), bold)
        self.apply_filter()

    def _refresh_item(self, item, bold) -> list[TerminalMonitor]:
        """Update one row (recursively); return the monitors below it."""
        below = []
        for index in range(item.childCount()):
            below += self._refresh_item(item.child(index), bold)
        port = item.data(COL_NAME, ROLE_PORT)
        if port is not None and port in self.monitors:
            monitor = self.monitors[port]
            self._paint_terminal(item, monitor, below)
            return [monitor] + below
        if below:
            self._paint_group(item, below, bold)
        return below

    def _paint_terminal(self, item, monitor, below=()):
        """
        One terminal row. State/Link text = the terminal's own values; the dot of a
        junction terminal (EP9128, EK1122, ...) also rolls up everything downstream of it.
        """
        health = max([monitor.health] + [m.health for m in below])
        item.setIcon(COL_NAME, self._dots[health])
        t = monitor.terminal
        tip = f"{t.name}\nType {t.type or '-'}\n{monitor.base}"
        if below:
            bad = sum(m.health != H_OK for m in below)
            tip += f"\n\nDownstream: {len(below)} terminal{'s' if len(below) != 1 else ''}, " + (
                f"{bad} not OK (dot shows the worst status below)" if bad else "all OK"
            )
        item.setToolTip(COL_NAME, tip)
        for col, text, good in (
            (COL_STATE, monitor.state_text, GOOD_STATE),
            (COL_LINK, monitor.link_text, GOOD_LINK),
        ):
            item.setText(col, text if text is not None else "DISCONNECTED")
            color = MUTED_GREY if text is None else None if text == good else FAULT_RED
            if col == COL_STATE and text is not None and monitor.state_flags:
                color = FAULT_RED  # e.g. OP with the ERROR flag
            _set_foreground(item, col, color)
        access, reasons = monitor.access
        item.setIcon(COL_ACCESS, self._locks[access])
        item.setToolTip(COL_ACCESS, access_tooltip(access, reasons))
        flags = monitor.state_flags
        flag_text = "flags: " + (" + ".join(flags) if flags else "none") if flags is not None else ""
        item.setToolTip(
            COL_STATE, "\n".join(filter(None, [monitor.state_text, flag_text, f"{monitor.base}:State_RBV"]))
        )
        item.setToolTip(
            COL_LINK, "\n".join(filter(None, [monitor.link_detail or monitor.link_text, f"{monitor.base}:Link_RBV"]))
        )

    def _paint_group(self, item, monitors, bold):
        total = len(monitors)
        disconnected = sum(m.health == H_DISCONNECTED for m in monitors)
        not_op = sum(m.state_text is not None and m.state_text != GOOD_STATE for m in monitors)
        bad_link = sum(m.link_text is not None and m.link_text != GOOD_LINK for m in monitors)
        accesses = [m.access[0] for m in monitors]
        editable = accesses.count("EDITABLE")
        unknown = accesses.count("UNKNOWN")
        worst = max(m.health for m in monitors)
        item.setIcon(COL_NAME, self._dots[worst])
        item.setFont(COL_NAME, bold)
        state = "DISCONNECTED" if disconnected else "ALL OP" if not_op == 0 else f"{not_op} NOT OP"
        link = "DISCONNECTED" if disconnected else "ALL OK" if bad_link == 0 else f"{bad_link} NOT OK"
        item.setToolTip(
            COL_STATE, f"{total - not_op - disconnected} of {total} in OP, {not_op} not OP, {disconnected} disconnected"
        )
        for col, text, good in ((COL_STATE, state, not_op == 0), (COL_LINK, link, bad_link == 0)):
            item.setText(col, text)
            color = MUTED_GREY if disconnected else None if good else FAULT_RED
            _set_foreground(item, col, color)
        group_access = "EDITABLE" if editable else "UNKNOWN" if unknown == total else "LOCKED"
        item.setIcon(COL_ACCESS, self._locks[group_access])
        item.setToolTip(COL_ACCESS, f"{editable} of {total} terminals editable")

    # ------------------------------------------------------------------ filter
    def _matches(self, monitor: TerminalMonitor, mode: int, text: str) -> bool:
        t = monitor.terminal
        if text and text not in f"{t.name} {t.type} {t.port}".lower():
            return False
        if mode == SHOW_FAULTS:
            return monitor.health != H_OK
        if mode == SHOW_NOT_OP:
            return monitor.state_text != GOOD_STATE
        if mode == SHOW_LINK:
            return monitor.link_text != GOOD_LINK
        if mode == SHOW_EDITABLE:
            return monitor.access[0] == "EDITABLE"
        if mode == SHOW_DISCONNECTED:
            return monitor.health == H_DISCONNECTED
        return True

    def _filter_active(self) -> bool:
        return self.showCombo.currentIndex() != SHOW_ALL or bool(self.filterEdit.text().strip())

    def _on_filter_changed(self, *_args):
        """Expand to reveal matches, or collapse back (keeping the selection visible) when cleared."""
        self.apply_filter()
        tree = self.terminalTree
        if self._filter_active():
            tree.expandAll()  # rows filtered out stay hidden
            return
        tree.collapseAll()
        current = tree.currentItem()
        if current is not None:
            _expand_parents(current)
            tree.scrollToItem(current)

    def apply_filter(self):
        mode = self.showCombo.currentIndex()
        text = self.filterEdit.text().strip().lower()
        tree = self.terminalTree
        for index in range(tree.topLevelItemCount()):
            self._filter_item(tree.topLevelItem(index), mode, text)

    def _filter_item(self, item, mode, text) -> bool:
        child_visible = False
        for index in range(item.childCount()):
            child_visible |= self._filter_item(item.child(index), mode, text)
        port = item.data(COL_NAME, ROLE_PORT)
        if port is not None and port in self.monitors:
            visible = child_visible or self._matches(self.monitors[port], mode, text)
        elif item.childCount():
            visible = child_visible
        else:
            visible = True  # message rows
        item.setHidden(not visible)
        return visible

    # ------------------------------------------------------------------ detail
    def select_terminal(self, port: int) -> bool:
        """Select a terminal by port (expands its parents); False if it is not in the tree."""
        item = self.terminal_items.get(port)
        if item is None:
            return False
        _expand_parents(item)
        self.terminalTree.setCurrentItem(item)
        self.terminalTree.scrollToItem(item)
        return True

    def _on_current_item_changed(self, current, _previous):
        port = current.data(COL_NAME, ROLE_PORT) if current is not None else None
        self._show_detail(self.monitors.get(port))

    def _show_detail(self, monitor: TerminalMonitor | None):
        """Show the selected terminal in the panel, through its existing monitor (no second subscription)."""
        widget = self.terminalWidget
        if monitor is None:
            widget.disconnect_channels()
            widget.setVisible(False)
            self.detailPlaceholder.setVisible(True)
            return
        widget.setProperty("confirmRequests", self._confirm)
        widget.set_monitor(monitor, self._prefix)
        self.detailPlaceholder.setVisible(False)
        widget.setVisible(True)
