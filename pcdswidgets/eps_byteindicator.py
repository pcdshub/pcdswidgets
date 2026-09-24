"""EPS byte indicator widget with per-bit tooltips."""

from pydm.widgets import PyDMByteIndicator, PyDMChannel
from pydm.widgets.display_format import DisplayFormat, parse_value_for_display
from qtpy.QtCore import Property, Qt
from qtpy.QtGui import QColor
from qtpy.QtWidgets import QTabWidget, QVBoxLayout, QWidget


class ByteIndicator_NegativeNums(PyDMByteIndicator):
    """
    Modified Byte Indicator Class.

    Overrides update_indicators function to allow for negative numbers to work
    for PyDmByteIndicator.
    """

    def update_indicators(self):
        """Update the indicator colors, allowing negative shift values."""
        if self._shift < 0:
            value = int(self.value) << abs(self._shift)
        else:
            value = int(self.value) >> self._shift

        bits = [(value >> i) & 1 for i in range(self._num_bits)]
        for bit, indicator in zip(bits, self._indicators, strict=False):
            if self._connected:
                if self._alarm_state == 3:
                    c = self._invalid_color
                else:
                    c = self._on_color if bit else self._off_color
            else:
                c = self._disconnected_color
            indicator.setColor(c)


class EPSByteIndicator(QWidget):
    """Widget for displaying EPS interlocks."""

    _qt_designer_ = {
        "group": "ECS EPS",
        "is_container": False,
    }

    template_widget: ByteIndicator_NegativeNums

    _channels_prefix = None
    _value_channel = None
    _label_channel = None

    _value_pv = ""
    _label_pv = ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.template_widget = ByteIndicator_NegativeNums()
        layout = QVBoxLayout()
        layout.addWidget(self.template_widget)
        self.setLayout(layout)

    def value_change(self, new_value):
        """Handle a value change from the value PV."""
        self.template_widget.value = new_value
        self.template_widget.update_indicators()

    def label_change(self, new_labels):
        """Handle a labels change from the label PV."""
        labels = parse_value_for_display(value=new_labels, precision=0, display_format_type=DisplayFormat.String)

        labels = labels.split(";")
        self.template_widget.numBits = len(labels)
        self.template_widget.labels = labels
        self.template_widget.update_indicators()

    def value_channel(self, connection):
        """Handle a connection state change on the value PV."""
        self.template_widget._connected = connection

    @Property(str)
    def channel(self):
        """Return the base PV prefix of the EPS structure."""
        return self._channels_prefix

    @channel.setter
    def channel(self, ch):
        """Set the base PV prefix of the EPS structure."""
        if ch != self._channels_prefix:
            self._value_pv = ch + ":nFlags_RBV"
            self._label_pv = ch + ":sFlagDesc_RBV"

            _value_channel = PyDMChannel(
                address=self._value_pv, connection_slot=self.value_channel, value_slot=self.value_change
            )

            _label_channel = PyDMChannel(address=self._label_pv, value_slot=self.label_change)
            _value_channel.connect()
            _label_channel.connect()

            self._channels_prefix = ch

    @Property(bool)
    def circles(self):
        """Return whether the byte indicators are drawn as circles."""
        return self.template_widget.circles

    @circles.setter
    def circles(self, circles):
        """Set whether the byte indicators are drawn as circles."""
        self.template_widget.circles = circles

    @Property(QTabWidget.TabPosition)
    def label_position(self):
        """Return the position of the labels relative to the indicators."""
        return self.template_widget._label_position

    @label_position.setter
    def label_position(self, position):
        """Set the position of the labels relative to the indicators."""
        self.template_widget._label_position = position
        self.template_widget.rebuild_layout()

    @Property(Qt.Orientation)
    def orientation(self):
        """Return the orientation of the indicator strip."""
        return self.template_widget._orientation

    @orientation.setter
    def orientation(self, orientation):
        """Set the orientation of the indicator strip."""
        self.template_widget._orientation = orientation
        self.template_widget.set_spacing()
        self.template_widget.rebuild_layout()

    @Property(QColor)
    def OnColor(self):
        """Return the color used for indicators in the on state."""
        return self.template_widget._on_color

    @OnColor.setter
    def OnColor(self, new_color):
        """Set the color used for indicators in the on state."""
        if self.template_widget._on_color != new_color:
            self.template_widget._on_color = new_color
            self.template_widget.update_indicators()

    @Property(QColor)
    def OffColor(self):
        """Return the color used for indicators in the off state."""
        return self.template_widget._off_color

    @OffColor.setter
    def OffColor(self, new_color):
        """Set the color used for indicators in the off state."""
        if self.template_widget._off_color != new_color:
            self.template_widget._off_color = new_color
            self.template_widget.update_indicators()
