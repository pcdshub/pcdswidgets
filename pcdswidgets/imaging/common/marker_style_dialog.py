"""Dialog for selecting marker display style and line thickness."""

from __future__ import annotations

from qtpy.QtWidgets import (
    QButtonGroup,
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


class MarkerStyleDialog(QDialog):
    """Popup dialog for configuring marker style and pen thickness.

    Parameters
    ----------
    current_style : MarkerStyle
        The currently active marker style (pre-selected in the dialog).
    current_width : int
        The current pen thickness in pixels.
    parent : QWidget, optional
        Parent widget.
    """

    def __init__(self, current_style: MarkerStyle, current_width: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Marker Style")
        self.setMinimumWidth(250)

        self._selected_style = current_style
        self._selected_width = current_width

        layout = QVBoxLayout(self)

        # ── Style selection ──────────────────────────────────────────────
        style_group = QGroupBox("Symbol Type")
        style_layout = QVBoxLayout(style_group)

        self._style_buttons = QButtonGroup(self)
        style_options = [
            (MarkerStyle.CROSSHAIR, "Crosshair (medium)"),
            (MarkerStyle.CROSSHAIR_SMALL, "Crosshair (small)"),
            (MarkerStyle.CROSSHAIR_LARGE, "Crosshair (large)"),
            (MarkerStyle.INFINITE_LINES, "Infinite lines"),
        ]
        for style, label in style_options:
            radio = QRadioButton(label)
            if style == current_style:
                radio.setChecked(True)
            self._style_buttons.addButton(radio, style.value)
            style_layout.addWidget(radio)

        layout.addWidget(style_group)

        # ── Thickness control ────────────────────────────────────────────
        thickness_group = QGroupBox("Line Thickness")
        thickness_layout = QHBoxLayout(thickness_group)
        thickness_layout.addWidget(QLabel("Width (px):"))
        self._thickness_spin = QSpinBox()
        self._thickness_spin.setRange(1, 20)
        self._thickness_spin.setValue(current_width)
        thickness_layout.addWidget(self._thickness_spin)

        layout.addWidget(thickness_group)

        # ── Buttons ──────────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")
        ok_btn.setDefault(True)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(ok_btn)
        layout.addLayout(btn_row)

        ok_btn.clicked.connect(self._accept)
        cancel_btn.clicked.connect(self.reject)

    def _accept(self):
        checked_id = self._style_buttons.checkedId()
        if checked_id >= 0:
            self._selected_style = MarkerStyle(checked_id)
        self._selected_width = self._thickness_spin.value()
        self.accept()

    @property
    def selected_style(self) -> MarkerStyle:
        return self._selected_style

    @property
    def selected_width(self) -> int:
        return self._selected_width
