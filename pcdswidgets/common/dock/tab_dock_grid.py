"""Overview of the Experimental Area"""

import collections
import functools
import logging
from typing import Callable, cast

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


class BaseDeviceButton(QPushButton):
    """Base class for QPushButton to show devices"""

    _OPEN_ALL = "Open All"

    devices: list

    def __init__(self, title, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title = title
        # References for created screens
        self._device_displays: dict[str, QWidget] = {}
        self._suite = None
        # Setup Menu
        self.setContextMenuPolicy(Qt.PreventContextMenu)
        self.device_menu = QMenuWithClickableSubmenu()
        self.device_menu.aboutToShow.connect(self._menu_shown)

    def show_device(self, device):
        if device.name not in self._device_displays:
            widget = display_for_device(device)
            widget.setParent(self)
            self._device_displays[device.name] = widget
        return self._device_displays[device.name]

    def show_all(self):
        """Create a widget for contained devices"""
        return [self.show_device(device=device) for device in self.devices]

    def get_all_titles(self):
        """Get the titles of each window, e.g. the name of each device."""
        return [device.name for device in self.devices]

    def _devices_shown(self, shown):
        """Implemeted by subclass"""
        pass

    def _menu_shown(self):
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
        sub_menu = self.device_menu.addMenu(text)
        TabDock.add_to_dock_user_menu(widget=widget_func, title=text, menu=sub_menu)
        sub_menu.setDefaultAction(sub_menu.actions()[0])
        self.device_menu.addMenu(sub_menu)

    def _show_device_wrapper(self, device):
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
    """Single Cell of Indicator Lights in the Overview Grid"""

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

    @property
    def matchable_names(self):
        """All names used for text searching"""
        return [self.title] + [device.name for device in self.devices]

    @Property(bool)  # type: ignore
    def selected(self) -> bool:
        """Whether the devices in this cell have been selected"""
        return bool(len(self._selecting_widgets))

    def add_indicator(self, widget):
        """Add an indicator to the Panel"""
        widget.setFixedSize(self.icon_size, self.icon_size)
        widget.setMinimumSize(self.icon_size, self.icon_size)
        self.layout().addWidget(widget)

    def add_device(self, device):
        """Add a device to the IndicatorCell"""
        indicator = indicator_for_device(device)
        indicator.setContextMenuPolicy(Qt.NoContextMenu)
        self.devices.append(device)
        self.add_indicator(indicator)

    def sizeHint(self):
        size_per_icon = self.icon_size + self.spacing
        return QSize(self.max_columns * size_per_icon + self.spacing + 2 * self.margin, 36)

    def _devices_shown(self, shown, selector=None):
        """Callback when corresponding ``TyphosSuite`` is accessed"""
        import typhos.utils

        selector = selector or self
        # On first selection
        if shown and selector not in self._selecting_widgets:
            self._selecting_widgets.append(selector)
            typhos.utils.reload_widget_stylesheet(self)
        # On closure
        elif not shown and selector in self._selecting_widgets:
            self._selecting_widgets.remove(selector)
            typhos.utils.reload_widget_stylesheet(self)


class IndicatorGroup(BaseDeviceButton):
    """QPushButton to select an entire row or column of devices"""

    def __init__(self, *args, orientation, **kwargs):
        super().__init__(*args, **kwargs)
        self.setText(str(self.title))
        self.cells = []
        self.installEventFilter(self)
        self.orientation = orientation

    def add_cell(self, cell):
        self.cells.append(cell)

    @property
    def devices(self) -> list:  # type: ignore
        """All devices contained in the ``IndicatorGroup``"""
        return [device for cell in self.cells for device in cell.devices]

    @property
    def device_to_indicator(self):
        """Dictionary of Device to IndicatorCell"""
        return {device: cell for cell in self.cells for device in cell.devices}

    def eventFilter(self, obj, event):  # type: ignore
        """Share QHoverEvents with all cells in the group"""
        if isinstance(event, QHoverEvent):
            for cell in self.cells:
                cell.event(event)
                return False
        return super().eventFilter(obj, event)

    def _devices_shown(self, shown):
        """Selecting this button, selects all contained cells"""
        for cell in self.cells:
            cell._devices_shown(shown, selector=self)


class IndicatorGrid(QWidget):
    """GridLayout of all Indicators"""

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.beamline = ""
        self.grid = QGridLayout()
        self.setLayout(self.grid)
        self.grid.setSpacing(0)
        self.grid.setSizeConstraint(QGridLayout.SetFixedSize)
        self._groups = {}
        self.setStyleSheet(
            """\
QWidget[selected="true"] {background-color: rgba(20, 140, 210, 150);}
            """
        )

    @property
    def groups(self):
        "A dictionary of name to IndicatorGroup"
        return dict(self._groups)

    def add_devices(self, devices, system=None, stand=None):
        # Create cell
        cell = IndicatorCell(title=f"{stand} {system}")
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

    def _add_group(self, group, as_row):
        # Add to layout
        group = IndicatorGroup(title=group, orientation="row" if as_row else "column")
        self._groups[group.title] = group
        # Find the correct position
        if as_row:
            (row, column) = (0, self.grid.columnCount())
        else:
            (row, column) = (self.grid.rowCount(), 0)
        self.grid.addWidget(group, row, column, Qt.AlignVCenter)

    def add_from_dict(self, devices=None):
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

    def load_happi(self):
        if not self.beamline:
            return
        self.loader = HappiLoader(
            beamline=self.beamline, group_keys=("location_group", "functional_group"), callbacks=[]
        )
        self.loader.start()


def get_happi_entry_value(entry, key):
    value = entry.metadata.get(key, None)
    if not value:
        raise ValueError(f"Invalid Key ({key} not in {entry}.")
    return value


class HappiLoader(QtCore.QThread):
    def __init__(self, *args, beamline, group_keys, callbacks, **kwargs):
        self.beamline = beamline
        self.group_keys = group_keys
        self.callbacks = callbacks
        super().__init__(*args, **kwargs)

    def _load_from_happi(self, row_group_key, col_group_key):
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
        row_group_key, col_group_key = self.group_keys

        dev_groups = self._load_from_happi(row_group_key, col_group_key)

        # Call the callback using the Receiver Slot Thread
        for cb in self.callbacks:
            f = functools.partial(cb, devices=dev_groups)
            QtCore.QTimer.singleShot(0, f)


device_display_cache = {}


def display_for_device(device):
    """Create a TyphosDeviceDisplay for a given device"""
    import typhos.display
    import typhos.utils

    try:
        return device_display_cache[device]
    except KeyError:
        ...
    with typhos.utils.no_device_lazy_load():
        logger.debug("Creating device display for %r", device)
        display = typhos.display.TyphosDeviceDisplay.from_device(device, scroll_option="scrollbar")
        typhos.utils.apply_standard_stylesheets(widget=display)
    device_display_cache[device] = display
    return display


_HAPPI_CLIENT = None


def get_happi_client():
    """
    Create and cache a happi client from configuration
    """
    global _HAPPI_CLIENT
    import happi

    if _HAPPI_CLIENT is None:
        _HAPPI_CLIENT = happi.Client.from_config()
    return _HAPPI_CLIENT


def indicator_for_device(device):  # type: ignore
    """Create a QWidget to indicate the alarm state of a QWidget"""
    import typhos.alarm

    try:
        hints = device.hints["fields"]
    except (AttributeError, KeyError):
        hints = []
    circle = typhos.alarm.TyphosAlarmCircle()  # type: ignore
    if hints:
        circle.kindLevel = typhos.alarm.TyphosAlarmCircle.KindLevel.HINTED  # type: ignore
    else:
        circle.kindLevel = typhos.alarm.TyphosAlarmCircle.KindLevel.NORMAL  # type: ignore
    circle.add_device(device)
    return circle
