from __future__ import annotations

import dataclasses
import functools
import json
import logging
from typing import Any, Callable

from pydm.utilities import is_qt_designer
from pydm.widgets import PyDMEmbeddedDisplay
from pydm.widgets.channel import PyDMChannel
from qtpy import QtCore, QtGui, QtWidgets

logger = logging.getLogger(__name__)


class FilterSortWidgetTable(QtWidgets.QTableWidget):
    """
    Displays repeated widgets that are sortable and filterable.

    This will allow you to sort or filter based on macros and based on the
    values in each pydm widget.
    """
    _qt_designer_ = {
        "group": "PCDS Utilities",
        "is_container": False,
    }

    # Public instance variables
    template_widget: PyDMEmbeddedDisplay

    # Private instance variables
    _ui_filename: str | None
    _macros_filename: str | None
    _macros: list[dict[str, str]]
    _channel_headers: list[str]
    _macro_headers: list[str]
    _header_map: dict[str, int]
    _channels: list[PyDMChannel]
    _filters: dict[str, FilterInfo]
    _initial_sort_header: str
    _initial_sort_ascend: bool
    _hide_headers: list[str]
    _configurable: bool
    _watching_cells: bool

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._ui_filename = None
        self._macros_filename = None
        self.template_widget = PyDMEmbeddedDisplay(parent=self)
        self.template_widget.hide()
        self.template_widget.loadWhenShown = False
        self._macros = []
        self._channel_headers = []
        self._macro_headers = []
        self._header_map = {}
        self._channels = []
        self._filters = {}
        self._initial_sort_header = 'index'
        self._initial_sort_ascend = True
        self._hide_headers = []

        # Table settings
        self.setShowGrid(True)
        self.setSortingEnabled(False)
        self.setSelectionMode(self.NoSelection)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().hide()

        self.configurable = False

        self._watching_cells = False

    def channels(self) -> list[PyDMChannel]:
        """
        Tell PyDM about our table channels so it knows to close them at exit.
        """
        return self._channels

    @QtCore.Property(str)
    def ui_filename(self) -> str:
        """
        Name of the ui file that is to be repeated to fill the table.

        This is currently required. When this is changed, we'll rebuild the
        table.
        """
        return self._ui_filename

    @ui_filename.setter
    def ui_filename(self, filename: str):
        self._ui_filename = filename
        self.reload_ui_file()
        self.reinit_table()

    def reload_ui_file(self) -> None:
        """
        Load the UI file and inspect it for PyDM channels.
        """
        try:
            self.template_widget.filename = self.ui_filename
        except Exception:
            logger.exception(
                "Reloading the UI file %s failed",
                self.ui_filename,
            )
            return
        # Let's find all the widgets with channels and save their names
        self._channel_headers = []
        for widget in self.template_widget.embedded_widget.children():
            try:
                ch = widget.channels()
            except Exception:
                # It is expected that some widgets do not have channels
                continue
            if ch:
                self._channel_headers.append(widget.objectName())

    @QtCore.Property(str)
    def macros_filename(self) -> str:
        """
        Json file defining PyDM macros. Optional.

        This follows the same format as used for the PyDM Template Repeater.
        If omitted, you should pass in macros using the set_macros method
        instead.
        """
        return self._macros_filename

    @macros_filename.setter
    def macros_filename(self, filename: str):
        self._macros_filename = filename
        self.reload_macros_file()

    def reload_macros_file(self) -> None:
        """
        Load the macros_filename and call set_macros.
        """
        if not self.macros_filename:
            return
        try:
            with open(self.macros_filename) as fd:
                macros = json.load(fd)
            self.set_macros(macros)
        except Exception:
            logger.exception('')
            return

    def set_macros(self, macros_list: list[dict[str, str]]) -> None:
        """
        Change the PyDM macros we use to load the table widgets.

        This causes the table to be rebuilt.

        Parameters
        ----------
        macros_list : list of dict
            A list where each element is a dictionary that defines the macros
            to pass in to one instance of the repeated widget. All dicts must
            have the same keys or this will not work properly.
        """
        self._macros = macros_list
        self._macro_headers = (
            list(self._macros[0].keys())
            if self._macros
            else []
        )
        self.reinit_table()

    def reinit_table(self) -> None:
        """
        Rebuild the table based on the ui_filename and the newest macros.
        """
        if self._watching_cells:
            self.cellChanged.disconnect(self.handle_item_changed)
            self._watching_cells = False
        for channel in self._channels:
            channel.disconnect()
        self._channels = []
        self.clear()
        self.clearContents()
        self.setRowCount(0)
        self._header_map = {}
        if not self._macros and self._channel_headers:
            return
        # Column 1 displays widget, 2 is index, the rest hold values
        ncols = 2 + len(self._channel_headers) + len(self._macro_headers)
        self.setColumnCount(ncols)
        for col in range(1, ncols):
            self.hideColumn(col)
        for macros in self._macros:
            self.add_row(macros)

        self._watching_cells = True
        self.cellChanged.connect(self.handle_item_changed)
        self.update_all_filters()

    def add_row(self, macros: dict[str, str]) -> None:
        """
        Adds a single row to the table.

        Each row will be created from the same UI file template.
        The macros used must have the same keys as all the previously
        added rows, or else the table will not work correctly.

        Parameters
        ----------
        macros : dict of str
            The macro substitutions for the UI file. These must be
            strings because we're effectively substituting them into
            the file's text.
        """
        widget = PyDMEmbeddedDisplay(parent=self)
        widget.macros = json.dumps(macros)
        widget.filename = self.ui_filename
        widget.loadWhenShown = False
        widget.disconnectWhenHidden = False
        self.add_context_menu_to_children(widget.embedded_widget)

        row_position = self.rowCount()
        self.insertRow(row_position)

        # Put the widget into the table
        self.setCellWidget(row_position, 0, widget)
        self._header_map['widget'] = 0
        self.setRowHeight(row_position, widget.height())

        # Put the index into the table
        item = ChannelTableWidgetItem(
            header='index',
            default=row_position,
        )
        self.setItem(row_position, 1, item)
        self._header_map['index'] = 1
        # Put the macros into the table
        index = 2
        for key, value in macros.items():
            item = ChannelTableWidgetItem(
                header=key,
                default=value,
            )
            self.setItem(row_position, index, item)
            self._header_map[key] = index
            index += 1
        # Set up the data columns and the channels
        for header in self._channel_headers:
            source = widget.findChild(QtCore.QObject, header)
            item = ChannelTableWidgetItem(
                header=header,
                channel=source.channel,
            )
            self.setItem(row_position, index, item)
            self._header_map[header] = index
            if item.pydm_channel is not None:
                self._channels.append(item.pydm_channel)
            index += 1

    def add_context_menu_to_children(self, widget: QtWidgets.QWidget) -> None:
        """
        Distribute the context menu to child widgets.

        This makes it so you can right click to configure the table from
        within any of the contained widgets.
        """
        for widget in widget.children():
            widget.contextMenuEvent = self.contextMenuEvent

    def contextMenuEvent(self, _event) -> None:
        """
        On right click, create and open a settings menu.
        """
        menu = QtWidgets.QMenu(parent=self)
        configure_action = menu.addAction('Configure')
        configure_action.setCheckable(True)
        configure_action.setChecked(self.configurable)
        configure_action.toggled.connect(self.request_configurable)
        active_sort_action = menu.addAction('Active Re-sort')
        active_sort_action.setCheckable(True)
        active_sort_action.setChecked(self.isSortingEnabled())
        active_sort_action.toggled.connect(self.setSortingEnabled)
        sort_menu = menu.addMenu('Sorting')
        for header_name in self._header_map.keys():
            if header_name == 'widget':
                continue
            if header_name in self.hide_headers_in_menu:
                continue
            inner_menu = sort_menu.addMenu(header_name.lower())
            asc = inner_menu.addAction('Ascending')
            asc.triggered.connect(
                functools.partial(
                    self.menu_sort,
                    header=header_name,
                    ascending=True,
                )
            )
            dec = inner_menu.addAction('Descending')
            dec.triggered.connect(
                functools.partial(
                    self.menu_sort,
                    header=header_name,
                    ascending=False,
                )
            )
        filter_menu = menu.addMenu('Filters')
        for filter_name, filter_info in self._filters.items():
            inner_action = filter_menu.addAction(filter_name)
            inner_action.setCheckable(True)
            inner_action.setChecked(filter_info.active)
            inner_action.toggled.connect(
                functools.partial(
                    self.activate_filter,
                    filter_name=filter_name,
                )
            )
        menu.exec_(QtGui.QCursor.pos())

    def get_row_values(self, row: int) -> dict[str, Any]:
        """
        Get the current values for a specific numbered row of the table.

        Parameters
        ----------
        row : int
            The row index to inspect. 0 is the current top row.

        Returns
        -------
        values : dict
            A mapping from str to value for each named widget in the template
            that has a PyDM channel. There is one additional special str, which
            is the 'connected' str, which is True if all channels are
            connected.
        """
        values = {'connected': True}
        for col in range(1, self.columnCount()):
            item = self.item(row, col)
            values[item.header] = item.get_value()
            if not item.connected:
                values['connected'] = False
        return values

    def add_filter(
        self,
        filter_name: str,
        filter_func: Callable[[dict[str, Any]], bool],
        active: bool = True
    ) -> None:
        """
        Add a new visibility filter to the table.

        Filters are functions with the following signature:
        ``filt(values: dict[str, Any]) -> bool``
        Where values is the output from get_row_values,
        and the boolean return value is True if the row should be displayed.
        If we have multiple filters, we need all of them to be True to display
        the row.

        Parameters
        ----------
        filter_name : str
            A name assigned to the filter to help us keep track of it.
        filter_func : func
            A callable with the correct signature.
        active : bool, optional.
            True if we want the filter to start as active. An inactive filter
            does not act on the table until the user requests it from the
            right-click context menu. Defaults to True.
        """
        # Filters take in a dict of values from header to value
        # Return True to show, False to hide
        self._filters[filter_name] = FilterInfo(
            filter_func=filter_func,
            active=active,
            name=filter_name,
        )
        self.update_all_filters()

    def remove_filter(self, filter_name: str) -> None:
        """
        Remove a specific named visibility filter from the table.

        This is a filter that was previously added using add_filter.

        Parameters
        ----------
        filter_name : str
            A name assigned to the filter to help us keep track of it.
        """
        del self._filters[filter_name]
        self.update_all_filters()

    def clear_filters(self) -> None:
        """
        Remove all visbility filters from the table.
        """
        self._filters = {}
        self.update_all_filters()

    def update_all_filters(self) -> None:
        """
        Apply all filters to all rows of the table.
        """
        for row in range(self.rowCount()):
            self.update_filter(row)

    def update_filter(self, row: int) -> None:
        """
        Apply all filters to one row of the table.

        Parameters
        ----------
        row : int
            The row index to inspect. 0 is the current top row.
        """
        if self._filters:
            values = self.get_row_values(row)
            show_row = []
            for filt_info in self._filters.values():
                if filt_info.active:
                    try:
                        should_show = filt_info.filter_func(values)
                    except Exception:
                        logger.debug(
                            'Error in filter function %s',
                            filt_info.name,
                            exc_info=True,
                        )
                        should_show = True
                    show_row.append(should_show)
                else:
                    # If inactive, record it as unfiltered/shown
                    show_row.append(True)
            if all(show_row):
                self.showRow(row)
            else:
                self.hideRow(row)
        else:
            self.showRow(row)

    def activate_filter(self, active: bool, filter_name: str) -> None:
        """
        Activate or deactivate a filter by name.

        Parameters
        ----------
        active : bool
            True if we want to activate a filter, False if we want to
            deactivate it.
        filter_name : str
            The name associated with the filter, chosen when we add the filter
            to the table.
        """
        self._filters[filter_name].active = active
        self.update_all_filters()

    def handle_item_changed(self, row: int, col: int) -> None:
        """
        Slot that is run when any element in the table changes.

        Currently, this updates the filters for the row that changed.
        """
        self.update_filter(row)

    @QtCore.Property(str)
    def initial_sort_header(self) -> str:
        """
        Column to sort on after initializing.

        Use this to initialize the sort order rather than using the sort_table
        function.
        """
        return self._initial_sort_header

    @initial_sort_header.setter
    def initial_sort_header(self, header: str):
        self._initial_sort_header = header
        if not is_qt_designer():
            # Do a sort after a short timer
            # HACK: this is because it doesn't work if done immediately
            # This is due to some combination of qt designer properties being
            # applied in some random order post-__init__ combined with it
            # taking a short bit of time for the items to be ready to sort.
            # Some items will never connect and never be ready to sort,
            # so for now we'll do a best-effort one-second wait.
            timer = QtCore.QTimer(parent=self)
            timer.singleShot(1000, self.initial_sort)

    @QtCore.Property(bool)
    def initial_sort_ascending(self) -> bool:
        """
        Whether to do the initial sort in ascending or descending order.
        """
        return self._initial_sort_ascend

    @initial_sort_ascending.setter
    def initial_sort_ascending(self, ascending: bool):
        self._initial_sort_ascend = ascending

    def initial_sort(self) -> None:
        """
        Called if the user specifies an initial_sort_header.
        """
        self.sort_table(self.initial_sort_header, self.initial_sort_ascending)

    @QtCore.Property('QStringList')
    def hide_headers_in_menu(self) -> list[str]:
        """
        A list of headers that we don't want to see in the sort menu.
        """
        return self._hide_headers

    @hide_headers_in_menu.setter
    def hide_headers_in_menu(self, headers: list[str]):
        self._hide_headers = headers

    def sort_table(self, header: str, ascending: bool) -> None:
        """
        Rearrange the ordering of the table based on any of the value fields.

        Parameters
        ----------
        header : str
            The name of any of the value fields to use to sort on. Valid
            headers are 'index', which is the original sort order, strings that
            match the macro keys, and strings that match widget names in the
            template.
        ascending : bool
            If True, we'll sort in ascending order. If False, we'll sort in
            descending order.
        """
        self.reset_manual_sort()
        if ascending:
            order = QtCore.Qt.AscendingOrder
        else:
            order = QtCore.Qt.DescendingOrder
        col = self._header_map[header]
        self.sortByColumn(col, order)

    def menu_sort(self, checked: bool, header: str, ascending: bool):
        """
        sort_table wrapped to recieve the checked bool from a signal.

        Ignore the checked boolean.
        """
        self.sort_table(header, ascending)

    def reset_manual_sort(self) -> None:
        """
        Rearrange the table to undo all manual drag/drop sorting.
        """
        header = self.verticalHeader()
        for row in range(self.rowCount()):
            header.moveSection(header.visualIndex(row), row)

    @QtCore.Property(bool, designable=False)
    def configurable(self) -> bool:
        """
        Whether or not the table can be manipulated from the UI.

        If True, the table rows can be dragged/dropped/rearranged.
        If False, the table rows can no longer be selected.

        This begins as False if unset and can be changed in the context menu.
        """
        return self._configurable

    @configurable.setter
    def configurable(self, conf: bool):
        self._configurable = conf
        if conf:
            self.verticalHeader().setSectionsMovable(True)
            self.verticalHeader().show()
        else:
            self.verticalHeader().setSectionsMovable(False)
            self.verticalHeader().hide()

    @QtCore.Slot(bool)
    def request_configurable(self, conf: bool):
        """
        Designable slot for toggling config mode.
        """
        self.configurable = conf


class ChannelTableWidgetItem(QtWidgets.QTableWidgetItem):
    """
    QTableWidgetItem that gets values from a PyDMChannel

    Parameters
    ----------
    header : str
        The name of the header of the column
    default : any, optional
        Starting value for the cell
    channel : str, optional
        PyDM channel address for value and connection updates.
    deadband : float, optional
        Only update the table if the change is more than the deadband.
        This can help make large tables less resource-hungry.
    """
    header: str
    channel: str | None
    deadband: float
    pydm_channel: PyDMChannel | None

    def __init__(
        self,
        header: str,
        default: Any | None = None,
        channel: str | None = None,
        deadband: float = 0.0,
        parent: QtWidgets.QWidget | None = None
    ):
        super().__init__(parent)
        self.header = header
        self.update_value(default)
        self.channel = channel
        self.deadband = deadband
        if channel is None:
            self.update_connection(True)
            self.pydm_channel = None
        else:
            self.update_connection(False)
            self.pydm_channel = PyDMChannel(
                channel,
                value_slot=self.update_value,
                connection_slot=self.update_connection,
            )
            self.pydm_channel.connect()

    def update_value(self, value: Any) -> str:
        """
        Store the value for sorting and display in the table if visible.

        By setting the text, we also notify the table that a cell has updated.
        """
        try:
            if abs(self._value - value) < self.deadband:
                return
        except Exception:
            pass
        self._value = value
        self.setText(str(value))

    def update_connection(self, connected: bool) -> None:
        """
        When our PV connects or disconnects, store the state as an attribute.
        """
        self.connected = connected

    def get_value(self) -> Any:
        return self._value

    def __lt__(self, other: ChannelTableWidgetItem) -> bool:
        """
        Two special sorting rules:
        1. None is the greatest
        2. Empty string is the greatest string

        This means that disconnected and empty string sort as "high"
        (sort ascending is most common)
        """
        # Make sure None sorts as greatest
        if self.get_value() is None:
            return False
        elif other.get_value() is None:
            return True
        # Make sure empty string sorts as next greatest
        elif self.get_value() == '':
            return False
        elif other.get_value() == '':
            return True
        return self.get_value() < other.get_value()


@dataclasses.dataclass
class FilterInfo:
    filter_func: Callable[[dict[str, Any]], bool]
    active: bool
    name: str
