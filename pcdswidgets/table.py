import dataclasses
import functools
import logging
import numbers
import simplejson as json
import typing

from pydm.widgets import PyDMEmbeddedDisplay
from pydm.widgets.channel import PyDMChannel
from PyQt5.QtGui import QTableWidget, QTableWidgetItem
from qtpy import QtCore, QtGui, QtWidgets

logger = logging.getLogger(__name__)


class FilterSortWidgetTable(QTableWidget):
    """
    Displays repeated widgets that are sortable and filterable.

    This will allow you to sort or filter based on macros and based on the
    values in each pydm widget.
    """
    def __init__(self, *args,  **kwargs):
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

        # Table settings
        self.setShowGrid(True)
        self.setSortingEnabled(False)
        self.setSelectionMode(self.NoSelection)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().hide()

        self.configurable = False

        self._watching_cells = False

    def channels(self):
        """
        Tell PyDM about our table channels so it knows to close them at exit.
        """
        return self._channels

    @QtCore.Property(str)
    def ui_filename(self):
        """
        Name of the ui file that is to be repeated to fill the table.

        This is currently required. When this is changed, we'll rebuild the
        table.
        """
        return self._ui_filename

    @ui_filename.setter
    def ui_filename(self, filename):
        self._ui_filename = filename
        self.reload_ui_file()
        self.reinit_table()

    def reload_ui_file(self):
        """
        Load the UI file and inspect it for PyDM channels.
        """
        try:
            self.template_widget.filename = self.ui_filename
        except Exception:
            logger.exception('')
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

    # file contains json list of dicts
    @QtCore.Property(str)
    def macros_filename(self):
        """
        Json file defining PyDM macros. Optional.

        This follows the same format as used for the PyDM Template Repeater.
        If omitted, you should pass in macros using the set_macros method
        instead.
        """
        return self._macros_filename

    @macros_filename.setter
    def macros_filename(self, filename):
        self._macros_filename = filename
        self.reload_macros_file()

    def reload_macros_file(self):
        """
        Load the macros_filename and call set_macros.
        """
        if not self.macros_filename:
            return
        try:
            with open(self.macros_filename, 'r') as fd:
                macros = json.load(fd)
            self.set_macros(macros)
        except Exception:
            logger.exception('')
            return

    def set_macros(self, macros_list):
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
        self._macro_headers = list(self._macros[0].keys())
        self.reinit_table()

    def reinit_table(self):
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
                self._channels.append(item.pydm_channel)
                index += 1

        self._watching_cells = True
        self.cellChanged.connect(self.handle_item_changed)
        self.update_all_filters()

    def add_context_menu_to_children(self, widget):
        for widget in widget.children():
            widget.contextMenuEvent = self.contextMenuEvent

    def contextMenuEvent(self, event):
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

    def get_row_values(self, row):
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

    def add_filter(self, filter_name, filter_func, active=True):
        """
        Add a new visibility filter to the table.

        Filters are functions with the following signature:
        filt(dict[str, Any]: values) -> bool
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

    def remove_filter(self, filter_name):
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

    def clear_filters(self):
        """
        Remove all visbility filters from the table.
        """
        self._filters = {}
        self.update_all_filters()

    def update_all_filters(self):
        """
        Apply all filters to all rows of the table.
        """
        for row in range(self.rowCount()):
            self.update_filter(row)

    def update_filter(self, row):
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
                    show_row.append(filt_info.filter_func(values))
                else:
                    # If inactive, record it as unfiltered/shown
                    show_row.append(True)
            if all(show_row):
                self.showRow(row)
            else:
                self.hideRow(row)
        else:
            self.showRow(row)

    def activate_filter(self, active, filter_name):
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

    def handle_item_changed(self, row, col):
        """
        Slot that is run when any element in the table changes.

        Currently, this updates the filters for the row that changed.
        """
        self.update_filter(row)

    def sort_table(self, header, ascending):
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
        self.sortItems(col, order)
        if not self.isSortingEnabled():
            self.setSortingEnabled(True)
            self.setSortingEnabled(False)

    def menu_sort(self, checked, header, ascending):
        """
        sort_table wrapped to recieve the checked bool from a signal.

        Ignore the checked boolean.
        """
        self.sort_table(header, ascending)

    def reset_manual_sort(self):
        """
        Rearrange the table to undo all manual drag/drop sorting.
        """
        header = self.verticalHeader()
        for row in range(self.rowCount()):
            header.moveSection(header.visualIndex(row), row)

    @QtCore.Property(bool)
    def configurable(self):
        """
        Whether or not the table can be manipulated from the UI.

        If True, the table rows can be dragged/dropped/rearranged.
        If False, the table rows can no longer be selected.

        This begins as False if unset.
        """
        return self._configurable

    @configurable.setter
    def configurable(self, conf):
        self._configurable = conf
        if conf:
            self.verticalHeader().setSectionsMovable(True)
            self.verticalHeader().show()
        else:
            self.verticalHeader().setSectionsMovable(False)
            self.verticalHeader().hide()

    @QtCore.Slot(bool)
    def request_configurable(self, conf):
        """
        Designable slot for toggling config mode.
        """
        self.configurable = conf


class ChannelTableWidgetItem(QTableWidgetItem):
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
    def __init__(self, header, default=None, channel=None, deadband=0,
                 parent=None):
        super().__init__(parent)
        self.header = header
        self.update_value(default)
        self.channel = channel
        self.deadband = deadband
        if channel is None:
            self.update_connection(True)
        else:
            self.update_connection(False)
            self.pydm_channel = PyDMChannel(
                channel,
                value_slot=self.update_value,
                connection_slot=self.update_connection,
                )
            self.pydm_channel.connect()

    def update_value(self, value):
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

    def update_connection(self, connected):
        """
        When our PV connects or disconnects, store the state as an attribute.
        """
        self.connected = connected

    def get_value(self):
        return self._value

    def __lt__(self, other):
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
    filter_func: typing.Callable[[dict], bool]
    active: bool
    name: str
