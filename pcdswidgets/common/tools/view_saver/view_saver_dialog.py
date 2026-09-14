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

    Provides fields for the save directory, file name, and the list of
    tracked widgets. Every registered property of a tracked widget is
    persisted, so the dialog operates on widget objectNames only.
    """

    def __init__(
        self,
        available_widgets: list[str],
        existing_widgets: list[str],
        dir_name: str,
        file_name: str,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Edit ViewSaver Settings")
        self.setMinimumWidth(450)

        self._available_widgets: list[str] = list(available_widgets)

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
        tool_tip = (
            "Name of the .ini file (without extension).\n"
            "Supports PyDM ${MACRO} expansion.\n"
            "Auto-generated if left empty."
        )
        name_label.setToolTip(tool_tip)
        self._name_edit = QLineEdit(file_name)
        self._name_edit.setToolTip(tool_tip)
        name_row.addWidget(name_label)
        name_row.addWidget(self._name_edit, stretch=1)
        file_layout.addLayout(name_row)

        layout.addWidget(file_group)

        # --- Tracked widgets group ---
        widget_list_group = QGroupBox("Tracked Widgets")
        bind_layout = QVBoxLayout(widget_list_group)

        self._list = QListWidget()
        self._list.setSelectionMode(QListWidget.ExtendedSelection)
        for name in existing_widgets:
            self._list.addItem(name)
        bind_layout.addWidget(self._list)

        # Widget selector combo
        combo_row = QHBoxLayout()
        self._widget_combo = QComboBox()
        self._widget_combo.setEditable(True)
        self._widget_combo.setInsertPolicy(QComboBox.NoInsert)
        self._widget_combo.setToolTip("Select a widget by its objectName.")
        self._widget_combo.addItems(self._available_widgets)

        add_btn = QPushButton("&Add")
        add_btn.setToolTip("Track the selected widget.")
        add_btn.clicked.connect(self._add_widget)

        add_all_btn = QPushButton("Add A&ll")
        add_all_btn.setToolTip("Track every discovered savable widget.")
        add_all_btn.clicked.connect(self._add_all)

        combo_row.addWidget(self._widget_combo, stretch=1)
        combo_row.addWidget(add_btn)
        combo_row.addWidget(add_all_btn)
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
        path = QFileDialog.getExistingDirectory(
            self, "Select Save Directory", self._dir_edit.text()
        )
        if path:
            self._dir_edit.setText(path)

    def _tracked_names(self) -> list[str]:
        return [self._list.item(i).text() for i in range(self._list.count())]

    def _add_name(self, name: str) -> None:
        if not name or name in self._tracked_names():
            return
        self._list.addItem(name)

    def _add_widget(self) -> None:
        self._add_name(self._widget_combo.currentText().strip())

    def _add_all(self) -> None:
        for name in self._available_widgets:
            self._add_name(name)

    def _remove_selected(self) -> None:
        for item in self._list.selectedItems():
            self._list.takeItem(self._list.row(item))

    def results(self) -> tuple[str, str, list[str]]:
        """Return ``(dir_name, file_name, tracked_widget_names)``."""
        return (
            self._dir_edit.text(),
            self._name_edit.text(),
            self._tracked_names(),
        )
