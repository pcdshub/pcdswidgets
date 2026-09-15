"""Dialog for editing ViewSaver settings in Qt Designer."""

from qtpy.QtCore import Qt
from qtpy.QtWidgets import (
    QDialog,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class ViewSaverDialog(QDialog):
    """Editor dialog for all ViewSaver settings.

    Provides fields for the save directory and file name, plus a checklist of
    the savable widgets discovered inside the container.  Every discovered
    widget is saved by default; unchecking one adds it to the excluded list so
    it is skipped.
    """

    def __init__(
        self,
        available_widgets: list[str],
        excluded_widgets: list[str],
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

        # --- Saved widgets group ---
        widget_list_group = QGroupBox("Saved Widgets")
        bind_layout = QVBoxLayout(widget_list_group)
        bind_layout.addWidget(QLabel("Widgets found inside this container. Uncheck any you do not want to persist."))

        self._list = QListWidget()
        excluded = set(excluded_widgets)
        for name in self._available_widgets:
            item = QListWidgetItem(name)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked if name in excluded else Qt.Checked)
            self._list.addItem(item)
        bind_layout.addWidget(self._list)

        # Check-all / uncheck-all convenience buttons.
        select_row = QHBoxLayout()
        check_all_btn = QPushButton("Save A&ll")
        check_all_btn.setToolTip("Persist every discovered widget.")
        check_all_btn.clicked.connect(lambda: self._set_all(Qt.Checked))
        uncheck_all_btn = QPushButton("Save &None")
        uncheck_all_btn.setToolTip("Exclude every discovered widget.")
        uncheck_all_btn.clicked.connect(lambda: self._set_all(Qt.Unchecked))
        select_row.addStretch()
        select_row.addWidget(check_all_btn)
        select_row.addWidget(uncheck_all_btn)
        bind_layout.addLayout(select_row)

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

    def _set_all(self, state: Qt.CheckState) -> None:
        for i in range(self._list.count()):
            self._list.item(i).setCheckState(state)

    def _excluded_names(self) -> list[str]:
        return [
            self._list.item(i).text()
            for i in range(self._list.count())
            if self._list.item(i).checkState() == Qt.Unchecked
        ]

    def results(self) -> tuple[str, str, list[str]]:
        """Return ``(dir_name, file_name, excluded_widget_names)``."""
        return (
            self._dir_edit.text(),
            self._name_edit.text(),
            self._excluded_names(),
        )
