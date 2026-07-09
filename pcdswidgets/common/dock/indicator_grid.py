"""
Grid of indicators representing devices in the experiment area.

This requires the optional "happi" and "typhos" dependencies to function at runtime,
but can be placed in designer without these installed.
It will also require any user modules used to define device types in the "happi"
database, such as "ophyd" and/or "pcdsdevices".

If a TabDock exists in the application, the grid will open "typhos" screens
in the dock, otherwise they will pop out as floating windows.
The standard keyboard shortcuts and right click options for dock windows
are supported.
"""

import collections
import functools
import logging
import textwrap
from typing import Any, Callable, Iterable, Protocol, cast

from pydm.utilities import is_qt_designer
from qtpy import QtCore
from qtpy.QtCore import QEvent, QSize, Qt
from qtpy.QtGui import QHoverEvent, QMouseEvent
from qtpy.QtWidgets import QGridLayout, QMenu, QPushButton, QWidget

from pcdswidgets.common.toolbar.yaml_toolbar import YamlTabLayout

from .tab_dock import TabDock

try:
    from qtpy.QtCore import Property  # type: ignore  # noqa: I001
except ImportError:
    from qtpy.QtCore import pyqtProperty as Property  # type: ignore  # noqa: I001

logger = logging.getLogger(__name__)


class Device(Protocol):
    """Type annotation stand-in for an ophyd Device (optional import)."""

    name: str


class Entry(Protocol):
    """Type annotation stand-in for a happi Entry (optional import)."""

    metadata: dict[str, Any]


# Type alias for the argument type required for callbacks in HappiLoader
HappiLoaderCbDict = dict[str, list[Device]]


class HappiLoaderCallback(Protocol):
    """Type annotation helper for HappiLoader-compatible callback functions."""

    def __call__(self, devices: HappiLoaderCbDict) -> None: ...


class BaseDeviceButton(QPushButton):
    """
    Base class for QPushButton to show devices.

    Child classes should populate the "devices" attribute, which is a list
    that contains all the typhos-compatible device objects to include in the button.

    All init parameters are passed directly through to QPushButton.
    """

    _OPEN_ALL = "Open All"

    devices: list[Device]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # References for created screens
        self._device_displays: dict[str, QWidget] = {}
        self._suite = None
        # Setup Menu
        self.setContextMenuPolicy(Qt.PreventContextMenu)
        self.device_menu = QMenuWithClickableSubmenu()
        self.device_menu.aboutToShow.connect(self._menu_shown)

    def show_device(self, device: Device) -> QWidget:
        """Return the typhos display for a device, creating it if necessary."""
        if device.name not in self._device_displays:
            widget = display_for_device(device)
            widget.setParent(self)
            self._device_displays[device.name] = widget
        return self._device_displays[device.name]

    def show_all(self) -> list[QWidget]:
        """Return the typhos displays for all devices, creating them if necessary."""
        return [self.show_device(device=device) for device in self.devices]

    def get_all_titles(self):
        """Return the titles of each window, e.g. the name of each device."""
        return [device.name for device in self.devices]

    def _menu_shown(self):
        """Update the right-click context menu when we need to show it."""
        # Current menu options
        menu_devices = [action.text() for action in self.device_menu.actions()]
        if self._OPEN_ALL not in menu_devices:
            sub_menu = self.device_menu.addMenu(self._OPEN_ALL)
            TabDock.add_many_to_dock_user_menu(
                widget_list=self.show_all,
                title_list=self.get_all_titles,
                menu=sub_menu,
            )
            self.device_menu.addMenu(sub_menu)
            self.device_menu.addSeparator()
        # Add devices
        for device in self.devices:
            if device.name not in menu_devices:
                # Add to device menu
                show_device = self._show_device_wrapper(device)
                self._add_to_menu(widget_func=show_device, text=device.name)

    def _add_to_menu(self, widget_func: Callable[[], QWidget], text: str):
        """Add a single device option to the menu."""
        sub_menu = self.device_menu.addMenu(text)
        TabDock.add_to_dock_user_menu(widget=widget_func, title=text, menu=sub_menu)
        sub_menu.setDefaultAction(sub_menu.actions()[0])
        self.device_menu.addMenu(sub_menu)

    def _show_device_wrapper(self, device: Device) -> Callable[[], QWidget]:
        """Helper for assembling the menus."""

        def inner():
            return self.show_device(device)

        return inner

    def eventFilter(self, obj, event):  # type: ignore
        """
        QWidget.eventFilter to be installed on child indicators

        This is required to display the :meth:`.contextMenuEvent` even if an
        indicator is pressed.
        """
        # Filter child widgets events to show context menu
        if event.type() == QEvent.MouseButtonPress:
            event = cast(QMouseEvent, event)
            if len(self.devices) == 0:
                # Important: don't do anything when there are no devices
                return False
            elif len(self.devices) == 1:
                device = self.devices[0]
                deferred_widget = self._show_device_wrapper(self.devices[0])
                if event.button() == Qt.LeftButton:
                    TabDock.add_to_dock_user_keybinds(widget=deferred_widget, title=device.name)
                    return True
                elif event.button() == Qt.RightButton:
                    TabDock.add_to_dock_user_menu(widget=deferred_widget, title=device.name, pos=event.globalPos())
                    return True
            elif event.button() in (Qt.LeftButton, Qt.RightButton):
                self.device_menu.exec_(event.globalPos())
                return True
        return False


class QMenuWithClickableSubmenu(QMenu):
    """
    QMenu, but we can click our submenus to do their default actions.
    """

    def mousePressEvent(self, event: QMouseEvent) -> None:  # type: ignore
        if event.button() == Qt.LeftButton:
            action = self.actionAt(event.pos())
            if action is None:
                return super().mousePressEvent(event)
            submenu_default_action = action.menu().defaultAction()
            if submenu_default_action is None:
                return super().mousePressEvent(event)
            submenu_default_action.trigger()
            self.close()
        else:
            return super().mousePressEvent(event)


class IndicatorCell(BaseDeviceButton):
    """
    Single Cell of Indicator Lights in the IndicatorGrid.

    In the grid, these are placed in the interior area (not the edges).
    This defines logic for including the circular indicators on the device buttons.

    All init args are passed through to BaseDeviceButton.
    """

    max_columns = 5
    icon_size = 12
    spacing = 1
    margin = 5

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Disable borders on the widget unless a hover occurs
        self.setStyleSheet("QPushButton:!hover {border: None}")
        self.setLayout(YamlTabLayout(self.max_columns))
        self.layout().setSpacing(self.spacing)
        self.layout().setContentsMargins(*4 * [self.margin])
        self._selecting_widgets = []
        self.installEventFilter(self)
        self.devices = []

    @Property(bool)  # type: ignore
    def selected(self) -> bool:
        """Whether the devices in this cell have been selected"""
        return bool(len(self._selecting_widgets))

    def add_indicator(self, widget: QWidget):
        """Add an indicator to the Panel"""
        widget.setFixedSize(self.icon_size, self.icon_size)
        widget.setMinimumSize(self.icon_size, self.icon_size)
        self.layout().addWidget(widget)

    def add_device(self, device: Device):
        """Add a device to the IndicatorCell"""
        indicator = indicator_for_device(device)
        indicator.setContextMenuPolicy(Qt.NoContextMenu)
        self.devices.append(device)
        self.add_indicator(indicator)

    def sizeHint(self):
        size_per_icon = self.icon_size + self.spacing
        return QSize(self.max_columns * size_per_icon + self.spacing + 2 * self.margin, 36)


class IndicatorGroup(BaseDeviceButton):
    """
    QPushButton to select an entire row or column of devices.

    In the grid, these are placed at the row and column headers.
    """

    def __init__(self, title: str, *args, orientation: str, **kwargs):
        super().__init__(*args, **kwargs)
        self.title = title
        self.setText(str(self.title))
        self.cells: list[IndicatorCell] = []
        self.installEventFilter(self)
        self.orientation = orientation

    def add_cell(self, cell: IndicatorCell):
        self.cells.append(cell)

    @property
    def devices(self) -> list[Device]:  # type: ignore
        """All devices contained in the ``IndicatorGroup``"""
        return [device for cell in self.cells for device in cell.devices]

    @property
    def device_to_indicator(self) -> dict[Device, IndicatorCell]:
        """Dictionary of Device to IndicatorCell"""
        return {device: cell for cell in self.cells for device in cell.devices}

    def eventFilter(self, obj, event):  # type: ignore
        """Share QHoverEvents with all cells in the group"""
        if isinstance(event, QHoverEvent):
            for cell in self.cells:
                cell.event(event)
                return False
        return super().eventFilter(obj, event)


class IndicatorGrid(QWidget):
    """
    Grid of all Indicators.

    This is the widget that goes in the screen.
    It can be parameterized only by setting the "beamline" property,
    which should be a valid "beamline" from happi, e.g. "TMO", "XPP", etc.

    This will search happi for every "active" device marked on that "beamline"
    and sort them into the grid by their "functional_group" and "location_group" keys.
    """

    _qt_designer_ = {
        "group": "ECS Common Dock",
        "is_container": False,
    }

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent=parent)
        self._beamline = ""
        self.grid = QGridLayout()
        self.setLayout(self.grid)
        self.grid.setSpacing(0)
        self.grid.setSizeConstraint(QGridLayout.SetFixedSize)
        self._groups: dict[str, IndicatorGroup] = {}
        self.setStyleSheet(
            textwrap.dedent(
                """
                QWidget[selected="true"] {background-color: rgba(20, 140, 210, 150);}
                """
            )
        )

    def set_beamline(self, beamline: str):
        """Set the beamline parameter, and in a live screen also load the devices from happi."""
        self._beamline = beamline
        if not is_qt_designer():
            self.load_happi(beamline)

    def get_beamline(self) -> str:
        """Return the beamline we've set."""
        return self._beamline

    beamline = Property("QString", get_beamline, set_beamline)

    def add_devices(self, devices: list[Device], system: str, stand: str):
        """Add many devices for a specific system/stand group to the grid."""
        # Create cell
        cell = IndicatorCell()
        for device in devices:
            cell.add_device(device)
        # Add to proper location in grid
        coords = []
        for i, group_name in enumerate((system, stand)):
            # Create the group if not present
            if group_name not in self._groups:
                self._add_group(group_name, bool(i))
            # Add cell to group
            # Coordinate of group
            group = self._groups[group_name]
            idx = self.grid.indexOf(group)
            coords.append(self.grid.getItemPosition(idx)[i])
            if cell:
                group.add_cell(cell)
        # Add cell to correct location in grid
        if cell:
            self.grid.addWidget(cell, coords[0], coords[1], Qt.AlignTop)

    def _add_group(self, group_name: str, as_row: bool):
        """Create a new IndicatorGroup and add it to the grid."""
        # Add to layout
        group = IndicatorGroup(title=group_name, orientation="row" if as_row else "column")
        self._groups[group.title] = group
        # Find the correct position
        if as_row:
            (row, column) = (0, self.grid.columnCount())
        else:
            (row, column) = (self.grid.rowCount(), 0)
        self.grid.addWidget(group, row, column, Qt.AlignVCenter)

    def add_from_dict(self, devices: HappiLoaderCbDict):
        """Add devices from the dict presented to HappiLoader callbacks."""
        rows = set()
        cols = set()
        if devices is None:
            return
        for e in devices:
            r, c = e.split("|")
            rows.add(r)
            cols.add(c)

        data = collections.OrderedDict()
        for r in sorted(rows):
            for c in sorted(cols):
                data[f"{r}|{c}"] = devices.get(f"{r}|{c}") or []

        for location, dev_list in data.items():
            stand, system = location.split("|")
            self.add_devices(dev_list, stand=stand, system=system)

    def load_happi(self, beamline: str):
        """Load happi devices into the grid using a background thread."""
        self.loader = HappiLoader(
            beamline=[beamline], group_keys=("location_group", "functional_group"), callbacks=[self.add_from_dict]
        )
        self.loader.start()


def get_happi_entry_value(entry: Entry, key: str) -> Any:
    value = entry.metadata.get(key, None)
    if not value:
        raise ValueError(f"Invalid Key ({key} not in {entry}.")
    return value


class HappiLoader(QtCore.QThread):
    """Thread for loading happi devices in the background."""

    def __init__(
        self,
        *args,
        beamline: Iterable[str],
        group_keys: tuple[str, str],
        callbacks: Iterable[HappiLoaderCallback],
        **kwargs,
    ):
        self.beamline = beamline
        self.group_keys = group_keys
        self.callbacks = callbacks
        super().__init__(*args, **kwargs)

    def _load_from_happi(self, row_group_key: str, col_group_key: str) -> HappiLoaderCbDict:
        """Fill with Data from Happi"""
        cli = get_happi_client()
        results = []
        for line in self.beamline:
            results += cli.search(beamline=line, active=True)

        dev_groups = collections.defaultdict(list)

        if not len(results):
            raise ValueError(f"Could not find entries for beamline {self.beamline}")

        import typhos

        with typhos.utils.no_device_lazy_load():
            for res in results:
                try:
                    stand = get_happi_entry_value(res, row_group_key)
                    system = get_happi_entry_value(res, col_group_key)
                    dev_obj = res.get(threaded=True)
                    dev_groups[f"{stand}|{system}"].append(dev_obj)
                except Exception:
                    logger.exception("Failed to load device %s", res)
                    continue
        return dev_groups

    def run(self):
        """When we start the thread, this runs in the background to load from happi and run callbacks."""
        row_group_key, col_group_key = self.group_keys

        dev_groups = self._load_from_happi(row_group_key, col_group_key)

        # Call the callback using the Receiver Slot Thread
        for cb in self.callbacks:
            f = functools.partial(cb, devices=dev_groups)
            QtCore.QTimer.singleShot(0, f)


device_display_cache = {}


def display_for_device(device: Device):
    """Create a TyphosDeviceDisplay for a given device"""
    # Embed optional dependency imports in function call
    from typhos.display import TyphosDeviceDisplay
    from typhos.utils import apply_standard_stylesheets, no_device_lazy_load

    try:
        return device_display_cache[device]
    except KeyError:
        ...
    with no_device_lazy_load():
        logger.debug("Creating device display for %r", device)
        display = TyphosDeviceDisplay.from_device(device, scroll_option="scrollbar")
        apply_standard_stylesheets(widget=display)
    device_display_cache[device] = display
    return display


_HAPPI_CLIENT = None


def get_happi_client():
    """Create and cache a happi client from configuration."""
    global _HAPPI_CLIENT
    # Embed optional dependency imports in function call
    import happi

    if _HAPPI_CLIENT is None:
        _HAPPI_CLIENT = happi.Client.from_config()
    return _HAPPI_CLIENT


def indicator_for_device(device):  # type: ignore
    """Create a QWidget to indicate the alarm state of a QWidget."""
    # Embed optional dependency imports in function call
    from typhos.alarm import TyphosAlarmCircle

    try:
        hints = device.hints["fields"]
    except (AttributeError, KeyError):
        hints = []
    circle = TyphosAlarmCircle()  # type: ignore
    if hints:
        circle.kindLevel = TyphosAlarmCircle.KindLevel.HINTED  # type: ignore
    else:
        circle.kindLevel = TyphosAlarmCircle.KindLevel.NORMAL  # type: ignore
    circle.add_device(device)
    return circle
