"""Dialog for configuring the centroid tracker's marker style, thickness, hatch pattern, and radius source."""

from qtpy.QtCore import Qt
from qtpy.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QVBoxLayout,
)

from pcdswidgets.imaging.common.cam_marker import MarkerStyle
from pcdswidgets.imaging.common.marker_style_dialog import HATCH_OPTIONS


class CentroidMarkerStyleDialog(QDialog):
    """Popup dialog for configuring the centroid tracker's marker.

    Unlike ``MarkerStyleDialog``, this only offers the symbol types relevant
    to a centroid tracker (infinite lines, an ellipse sized from the beam
    width, or both together), and lets the user choose whether the ellipse
    radius should track the live sigma readback or use a fixed default
    instead. There is also no "apply to all" option, since the centroid
    tracker only ever has a single marker.

    Parameters
    ----------
    current_style : MarkerStyle
        The currently active marker style (pre-selected in the dialog).
        Expected to be ``MarkerStyle.INFINITE_LINES``, ``MarkerStyle.ELLIPSE``,
        or ``MarkerStyle.INFINITE_LINES_AND_ELLIPSE``.
    current_width : int
        The current pen thickness in pixels.
    current_hatch_pattern : Qt.PenStyle
        The current line hatch pattern.
    current_use_sigma_radius : bool
        Whether the ellipse radius currently tracks the live sigma readback.
    current_default_radius : int
        The fixed radius (applied to both axes) used when not tracking sigma.
    parent : QWidget, optional
        Parent widget.
    """

    def __init__(
        self,
        current_style: MarkerStyle,
        current_width: int,
        current_hatch_pattern: Qt.PenStyle = Qt.SolidLine,
        current_use_sigma_radius: bool = True,
        current_default_radius: int = 20,
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Centroid Marker Style")
        self.setMinimumWidth(280)

        self._selected_style = current_style
        self._selected_width = current_width
        self._selected_hatch_pattern = current_hatch_pattern
        self._selected_use_sigma_radius = current_use_sigma_radius
        self._selected_default_radius = current_default_radius

        layout = QVBoxLayout(self)

        # ── Style selection ──────────────────────────────────────────────
        style_group = QGroupBox("Symbol Type")
        style_layout = QVBoxLayout(style_group)

        self._style_buttons = QButtonGroup(self)
        self._radio_infinite = QRadioButton("Infinite lines")
        self._radio_ellipse = QRadioButton("Ellipse")
        self._radio_infinite_ellipse = QRadioButton("Infinite lines + Ellipse")
        self._style_buttons.addButton(self._radio_infinite, MarkerStyle.INFINITE_LINES.value)
        self._style_buttons.addButton(self._radio_ellipse, MarkerStyle.ELLIPSE.value)
        self._style_buttons.addButton(self._radio_infinite_ellipse, MarkerStyle.INFINITE_LINES_AND_ELLIPSE.value)

        if current_style == MarkerStyle.INFINITE_LINES:
            self._radio_infinite.setChecked(True)
        elif current_style == MarkerStyle.INFINITE_LINES_AND_ELLIPSE:
            self._radio_infinite_ellipse.setChecked(True)
        else:
            self._radio_ellipse.setChecked(True)

        style_layout.addWidget(self._radio_infinite)
        style_layout.addWidget(self._radio_ellipse)
        style_layout.addWidget(self._radio_infinite_ellipse)

        # ── Ellipse radius source ────────────────────────────────────────
        self._use_sigma_checkbox = QCheckBox("Use sigma for radius")
        self._use_sigma_checkbox.setChecked(current_use_sigma_radius)
        style_layout.addWidget(self._use_sigma_checkbox)

        self._default_radius_row = QHBoxLayout()
        self._default_radius_label = QLabel("Default radius (px):")
        self._default_radius_spin = QSpinBox()
        self._default_radius_spin.setRange(1, 500)
        self._default_radius_spin.setValue(current_default_radius)
        self._default_radius_row.addWidget(self._default_radius_label)
        self._default_radius_row.addWidget(self._default_radius_spin)
        style_layout.addLayout(self._default_radius_row)

        layout.addWidget(style_group)

        self._style_buttons.idToggled.connect(self._update_controls_visibility)
        self._use_sigma_checkbox.toggled.connect(self._update_controls_visibility)
        self._update_controls_visibility()

        hatch_group = QGroupBox("Line Hatch Pattern")
        hatch_layout = QHBoxLayout(hatch_group)
        hatch_layout.addWidget(QLabel("Pattern:"))
        self._hatch_combo = QComboBox()
        for label, _pen_style in HATCH_OPTIONS:
            self._hatch_combo.addItem(label)
        # Pre-select current pattern
        for i, (_label, pen_style) in enumerate(HATCH_OPTIONS):
            if pen_style == current_hatch_pattern:
                self._hatch_combo.setCurrentIndex(i)
                break
        hatch_layout.addWidget(self._hatch_combo)

        layout.addWidget(hatch_group)

        thickness_group = QGroupBox("Line Thickness")
        thickness_layout = QHBoxLayout(thickness_group)
        thickness_layout.addWidget(QLabel("Width (px):"))
        self._thickness_spin = QSpinBox()
        self._thickness_spin.setRange(1, 20)
        self._thickness_spin.setValue(current_width)
        thickness_layout.addWidget(self._thickness_spin)

        layout.addWidget(thickness_group)

        btn_row = QHBoxLayout()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")
        ok_btn.setDefault(True)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(ok_btn)
        layout.addLayout(btn_row)

        ok_btn.clicked.connect(self._accept)
        cancel_btn.clicked.connect(self.reject)

    def _update_controls_visibility(self, *_args) -> None:
        has_ellipse = self._radio_ellipse.isChecked() or self._radio_infinite_ellipse.isChecked()
        self._use_sigma_checkbox.setVisible(has_ellipse)

        show_default_radius = has_ellipse and not self._use_sigma_checkbox.isChecked()
        self._default_radius_label.setVisible(show_default_radius)
        self._default_radius_spin.setVisible(show_default_radius)

    def _accept(self):
        checked_id = self._style_buttons.checkedId()
        if checked_id >= 0:
            self._selected_style = MarkerStyle(checked_id)
        self._selected_width = self._thickness_spin.value()
        hatch_idx = self._hatch_combo.currentIndex()
        self._selected_hatch_pattern = HATCH_OPTIONS[hatch_idx][1]
        self._selected_use_sigma_radius = self._use_sigma_checkbox.isChecked()
        self._selected_default_radius = self._default_radius_spin.value()
        self.accept()

    @property
    def selected_style(self) -> MarkerStyle:
        return self._selected_style

    @property
    def selected_width(self) -> int:
        return self._selected_width

    @property
    def selected_hatch_pattern(self) -> Qt.PenStyle:
        return self._selected_hatch_pattern

    @property
    def use_sigma_radius(self) -> bool:
        return self._selected_use_sigma_radius

    @property
    def selected_default_radius(self) -> int:
        return self._selected_default_radius
