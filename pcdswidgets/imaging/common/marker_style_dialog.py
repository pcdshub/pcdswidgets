"""Dialog for selecting marker display style, line thickness, hatch pattern, and arm length."""

from __future__ import annotations

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

_HATCH_OPTIONS: list[tuple[str, Qt.PenStyle]] = [
    ("Solid", Qt.SolidLine),
    ("Dotted", Qt.DotLine),
    ("Dashed", Qt.DashLine),
    ("DashDot", Qt.DashDotLine),
]


class MarkerStyleDialog(QDialog):
    """Popup dialog for configuring marker style, thickness, hatch pattern, and arm length.

    Parameters
    ----------
    current_style : MarkerStyle
        The currently active marker style (pre-selected in the dialog).
    current_width : int
        The current pen thickness in pixels.
    current_arm_length : int
        The current crosshair arm length in pixels.
    current_hatch_pattern : Qt.PenStyle
        The current line hatch pattern.
    parent : QWidget, optional
        Parent widget.
    """

    def __init__(
        self,
        current_style: MarkerStyle,
        current_width: int,
        current_arm_length: int = 20,
        current_hatch_pattern: Qt.PenStyle = Qt.SolidLine,
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Marker Style")
        self.setMinimumWidth(280)

        self._selected_style = current_style
        self._selected_width = current_width
        self._selected_arm_length = current_arm_length
        self._selected_hatch_pattern = current_hatch_pattern

        layout = QVBoxLayout(self)

        # ── Style selection ──────────────────────────────────────────────
        style_group = QGroupBox("Symbol Type")
        style_layout = QVBoxLayout(style_group)

        self._style_buttons = QButtonGroup(self)
        self._radio_length = QRadioButton("Crosshair (configurable length)")
        self._radio_infinite = QRadioButton("Infinite lines")
        self._style_buttons.addButton(self._radio_length, MarkerStyle.CROSSHAIR_LENGTH.value)
        self._style_buttons.addButton(self._radio_infinite, MarkerStyle.INFINITE_LINES.value)

        if current_style == MarkerStyle.INFINITE_LINES:
            self._radio_infinite.setChecked(True)
        else:
            self._radio_length.setChecked(True)

        style_layout.addWidget(self._radio_length)
        style_layout.addWidget(self._radio_infinite)

        self._arm_length_row = QHBoxLayout()
        self._arm_length_label = QLabel("Arm length (px):")
        self._arm_length_spin = QSpinBox()
        self._arm_length_spin.setRange(5, 500)
        self._arm_length_spin.setValue(current_arm_length)
        self._arm_length_row.addWidget(self._arm_length_label)
        self._arm_length_row.addWidget(self._arm_length_spin)
        style_layout.addLayout(self._arm_length_row)

        layout.addWidget(style_group)

        self._style_buttons.idToggled.connect(self._on_style_toggled)
        self._update_arm_length_visibility()

        hatch_group = QGroupBox("Line Hatch Pattern")
        hatch_layout = QHBoxLayout(hatch_group)
        hatch_layout.addWidget(QLabel("Pattern:"))
        self._hatch_combo = QComboBox()
        for label, _pen_style in _HATCH_OPTIONS:
            self._hatch_combo.addItem(label)
        # Pre-select current pattern
        for i, (_label, pen_style) in enumerate(_HATCH_OPTIONS):
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

        self._apply_all_checkbox = QCheckBox("Apply to all markers")
        layout.addWidget(self._apply_all_checkbox)

        btn_row = QHBoxLayout()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")
        ok_btn.setDefault(True)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(ok_btn)
        layout.addLayout(btn_row)

        ok_btn.clicked.connect(self._accept)
        cancel_btn.clicked.connect(self.reject)

    def _on_style_toggled(self, _id: int, _checked: bool) -> None:
        self._update_arm_length_visibility()

    def _update_arm_length_visibility(self) -> None:
        visible = self._radio_length.isChecked()
        self._arm_length_label.setVisible(visible)
        self._arm_length_spin.setVisible(visible)

    def _accept(self):
        checked_id = self._style_buttons.checkedId()
        if checked_id >= 0:
            self._selected_style = MarkerStyle(checked_id)
        self._selected_width = self._thickness_spin.value()
        self._selected_arm_length = self._arm_length_spin.value()
        hatch_idx = self._hatch_combo.currentIndex()
        self._selected_hatch_pattern = _HATCH_OPTIONS[hatch_idx][1]
        self.accept()

    @property
    def selected_style(self) -> MarkerStyle:
        return self._selected_style

    @property
    def selected_width(self) -> int:
        return self._selected_width

    @property
    def selected_arm_length(self) -> int:
        return self._selected_arm_length

    @property
    def selected_hatch_pattern(self) -> Qt.PenStyle:
        return self._selected_hatch_pattern

    @property
    def apply_to_all(self) -> bool:
        return self._apply_all_checkbox.isChecked()
