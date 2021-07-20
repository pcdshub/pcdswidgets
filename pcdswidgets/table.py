import logging
import simplejson as json

from pydm.widgets import PyDMEmbeddedDisplay
from pydm.widgets.channel import PyDMChannel
from PyQt5.QtGui import QTableWidget, QTableWidgetItem
from qtpy import QtCore

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
        self._dummy_widget = PyDMEmbeddedDisplay(parent=self)
        self._dummy_widget.hide()
        self._dummy_widget.loadWhenShown = False
        self._macros = []
        self._channel_headers = []
        self._macro_headers = []
        self._channels = []
        self._filters = {}

        # Table settings
        self.setShowGrid(True)
        self.setSortingEnabled(True)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().hide()
        self.verticalHeader().hide()

        self._watching_cells = False

    def channels(self):
        return self._channels

    @QtCore.Property(str)
    def ui_filename(self):
        return self._ui_filename

    @ui_filename.setter
    def ui_filename(self, filename):
        self._ui_filename = filename
        self.reload_ui_file()
        self.reinit_table()

    def reload_ui_file(self):
        try:
            self._dummy_widget.filename = self.ui_filename
        except Exception:
            logger.exception('')
        # Let's find all the widgets with channels and save their names
        self._channel_headers = []
        for widget in self._dummy_widget.embedded_widget.children():
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
        return self._macros_filename

    @macros_filename.setter
    def macros_filename(self, filename):
        self._macros_filename = filename
        self.reload_macros_file()

    def reload_macros_file(self):
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
        self._macros = macros_list
        self._macro_headers = list(self._macros[0].keys())
        self.reinit_table()

    def reinit_table(self):
        if self._watching_cells:
            self.cellChanged.disconnect(self.handle_item_changed)
            self._watching_cells = False
        for channel in self._channels:
            channel.disconnect()
            self._channels = []
        self.clear()
        self.clearContents()
        self.setRowCount(0)
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

            row_position = self.rowCount()
            self.insertRow(row_position)

            # Put the widget into the table
            self.setCellWidget(row_position, 0, widget)
            self.setRowHeight(row_position, widget.height())

            # Put the index into the table
            item = ChannelTableWidgetItem(
                header='index',
                default=row_position,
                )
            self.setItem(row_position, 1, item)
            # Put the macros into the table
            index = 2
            for key, value in macros.items():
                item = ChannelTableWidgetItem(
                    header=key,
                    default=value,
                    )
                self.setItem(row_position, index, item)
                index += 1
            # Set up the data columns and the channels
            for header in self._channel_headers:
                source = widget.findChild(QtCore.QObject, header)
                item = ChannelTableWidgetItem(
                    header=header,
                    channel=source.channel,
                    )
                self.setItem(row_position, index, item)
                self._channels.append(item.pydm_channel)
                index += 1

        self._watching_cells = True
        self.cellChanged.connect(self.handle_item_changed)
        self.update_all_filters()

    def get_row_values(self, row):
        values = {'connected': True}
        for col in range(1, self.columnCount()):
            item = self.item(row, col)
            values[item.header] = item.get_value()
            if not item.connected:
                values['connected'] = False
        return values

    def add_filter(self, filter_name, filt):
        # Filters take in a dict of values from header to value
        # Return True to show, False to hide
        self._filters[filter_name] = filt
        self.update_all_filters()

    def update_all_filters(self):
        if self._filters:
            for row in range(self.rowCount()):
                self.update_filter(row)

    def update_filter(self, row):
        if self._filters:
            values = self.get_row_values(row)
            show_row = []
            for filt in self._filters.values():
                show_row.append(filt(values))
            if all(show_row):
                self.showRow(row)
            else:
                self.hideRow(row)

    def handle_item_changed(self, row, col):
        self.update_filter(row)


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
    """
    def __init__(self, header, default=None, channel=None, parent=None):
        super().__init__(parent)
        self.header = header
        if default is None:
            self._value = None
        else:
            self.update_value(default)
        self.channel = channel
        self._type = None
        if channel is None:
            self.connected = True
        else:
            self.connected = False
            self.pydm_channel = PyDMChannel(
                channel,
                value_slot=self.update_value,
                connection_slot=self.update_connection,
                )
            self.pydm_channel.connect()

    def update_value(self, value):
        """
        Store the value for sorting and display in the table if visible
        """
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
        # Make sure None sorts as greatest
        if self.get_value() is None:
            return False
        elif other.get_value() is None:
            return True
        return self.get_value() < other.get_value()

