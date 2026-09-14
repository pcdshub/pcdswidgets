"""Dialog for editing ViewSaver settings in Qt Designer."""

from __future__ import annotations

from qtpy.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

class ViewSaverDialog(QDialog):
    """Editor dialog for all ViewSaver settings.

    Provides fields for the save directory, file name, and widget bindings.
    """

    def __init__(
        self,
        widget_specs: list[tuple[str, list[str]]],
        existing_widgets: list[str],
        dir_name: str,
        file_name: str,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Edit ViewSaver Settings")
        self.setMinimumWidth(450)

        self._widget_specs: dict[str, list[str]] = {name: props for name, props in widget_specs}

        layout = QVBoxLayout(self)

        # --- File settings group ---
        file_group = QGroupBox("Save Location")
        file_layout = QVBoxLayout(file_group)

        # Directory
        dir_row = QHBoxLayout()
        dir_label = QLabel("Directory:")
        dir_tooltip = "Folder where the .ini settings file will be stored."
        dir_label.setToolTip(dir_tooltip)
        self._dir_edit = QLineEdit(dir_name)
        self._dir_edit.setToolTip(dir_tooltip)
        dir_browse = QPushButton("Browse\u2026")
        dir_browse.setToolTip("Open a file dialog to pick the save directory.")
        dir_browse.clicked.connect(self._browse_dir)
        dir_row.addWidget(dir_label)
        dir_row.addWidget(self._dir_edit, stretch=1)
        dir_row.addWidget(dir_browse)
        file_layout.addLayout(dir_row)

        # Filename
        name_row = QHBoxLayout()
        name_label = QLabel("File name:")
        tool_tip =(
            "Name of the .ini file (without extension).\n"
            "Supports PyDM ${MACRO} expansion.\n"
            "Auto-generated if left empty."
        )
        name_label.setToolTip(tool_tip)
        self._name_edit = QLineEdit(file_name)
        self._name_edit.setToolTip(tool_tip )
        name_row.addWidget(name_label)
        name_row.addWidget(self._name_edit, stretch=1)
        file_layout.addLayout(name_row)

        layout.addWidget(file_group)

        # --- Bindings group ---
        widget_list_group = QGroupBox("Tracked Widgets")
        bind_layout = QVBoxLayout(widget_list_group)

        self._list = QListWidget()
        for b in existing_widgets:
            self._list.addItem(b)
        bind_layout.addWidget(self._list)

        # Widget / property combos
        combo_row = QHBoxLayout()
        self._widget_combo = QComboBox()
        self._widget_combo.setEditable(True)
        self._widget_combo.setInsertPolicy(QComboBox.NoInsert)
        self._widget_combo.setToolTip("Select a widget by its objectName.")
        self._widget_combo.addItems(sorted(self._widget_specs.keys()))
        self._widget_combo.currentTextChanged.connect(self._on_widget_changed)

        self._prop_combo = QComboBox()
        self._prop_combo.setEditable(True)
        self._prop_combo.setInsertPolicy(QComboBox.NoInsert)
        self._prop_combo.setToolTip("Select a savable property for the chosen widget.")
        self._on_widget_changed(self._widget_combo.currentText())

        add_btn = QPushButton("&Add")
        add_btn.clicked.connect(self._add_binding)

        combo_row.addWidget(self._widget_combo, stretch=2)
        combo_row.addWidget(self._prop_combo, stretch=1)
        combo_row.addWidget(add_btn)
        bind_layout.addLayout(combo_row)

        remove_btn = QPushButton("&Remove Selected")
        remove_btn.clicked.connect(self._remove_selected)
        bind_layout.addWidget(remove_btn)

        layout.addWidget(widget_list_group)

        # --- OK / Cancel ---
        button_row = QHBoxLayout()
        button_row.addStretch()
        cancel_btn = QPushButton("&Cancel")
        cancel_btn.clicked.connect(self.reject)
        ok_btn = QPushButton("&OK")
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(self.accept)
        button_row.addWidget(cancel_btn)
        button_row.addWidget(ok_btn)
        layout.addLayout(button_row)

    # ------------------------------------------------------------------

    def _browse_dir(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Select Save Directory", self._dir_edit.text())
        if path:
            self._dir_edit.setText(path)

    def _on_widget_changed(self, name: str) -> None:
        self._prop_combo.clear()
        props = self._widget_specs.get(name, [])
        self._prop_combo.addItems(props)

    def _add_binding(self) -> None:
        obj = self._widget_combo.currentText().strip()
        prop = self._prop_combo.currentText().strip()
        if not obj or not prop:
            return
        entry = f"{obj}::{prop}"
        for i in range(self._list.count()):
            if self._list.item(i).text() == entry:
                return
        self._list.addItem(entry)

    def _remove_selected(self) -> None:
        for item in self._list.selectedItems():
            self._list.takeItem(self._list.row(item))

    def results(self) -> str:
        return (
            self._dir_edit.text(),
            self._name_edit.text(),
            self._list
        )
