"""
Helper for using designer to layout widgets.
"""

from string import Template
from typing import Any, ClassVar, Protocol

from pydm.utilities.iconfont import IconFont
from pydm.widgets.base import PyDMPrimitiveWidget
from pydm.widgets.qtplugin_extensions import RulesExtension
from qtpy.QtWidgets import QAction, QDialog, QFormLayout, QHBoxLayout, QLineEdit, QPushButton, QVBoxLayout, QWidget

ifont = IconFont()


class _UiForm(Protocol):
    def setupUi(self, Form): ...

    def retranslateUi(self, Form): ...


class DesignerWidget(QWidget, PyDMPrimitiveWidget):  # type: ignore
    """Helper class for converting pydm displays for embedding to standalone widgets."""

    # Loaded from uic
    ui_form: ClassVar[type[_UiForm]]
    # Tells PyDM to include in designer
    _qt_designer_: dict[str, Any]
    # Macro name to widget names that include that macro
    _macro_to_widget: ClassVar[dict[str, list[str]]]
    # Widget name to required macros: all must be non-empty before updating
    _widget_to_macro: ClassVar[dict[str, list[str]]]
    # Widget name to per-property template to fill
    _widget_to_pre_template: ClassVar[dict[str, list[tuple[str, str | list[str]]]]]
    # Current values for each macro
    _macro_values: dict[str, str]

    def __init_subclass__(cls):
        super().__init_subclass__()
        # Extend the _qt_designer_ marker if it exists to include a quick editor for macro vals
        new_ext = [MacroEditExtension, RulesExtension]
        try:
            cls._qt_designer_["extensions"].extend(new_ext)
        except (AttributeError, KeyError):
            try:
                cls._qt_designer_["extensions"] = new_ext
            except AttributeError:
                ...
        # Interpret strings as icons so we don't have to import IconFont everywhere
        try:
            if isinstance(cls._qt_designer_["icon"], str):
                cls._qt_designer_["icon"] = ifont.icon(cls._qt_designer_["icon"])
        except (AttributeError, KeyError):
            ...

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui_form.setupUi(self, self)  # type: ignore

    def retranslateUi(self, *args, **kwargs):
        """Required function for setupUi to work in __init__"""
        self.ui_form.retranslateUi(self, *args, **kwargs)  # type: ignore

    def _get_macro(self, macro_name: str) -> str:
        return self._macro_values[macro_name]

    def _set_macro(self, macro_name: str, value: str):
        self._macro_values[macro_name] = value
        self._updates_for_macro(macro_name)

    def _updates_for_macro(self, macro_name: str):
        for widget_name in self._macro_to_widget[macro_name]:
            self._update_widget_for_macros(widget_name)

    def _update_widget_for_macros(self, widget_name: str):
        needed_macros = self._widget_to_macro[widget_name]
        if not all(self._macro_values[macro_name] for macro_name in needed_macros):
            # Skip! Not ready!
            return
        widget = getattr(self, widget_name)
        if not isinstance(widget, QWidget):
            raise TypeError(f"{widget_name} is not a widget: {widget}")
        for prop, templ in self._widget_to_pre_template[widget_name]:
            if isinstance(templ, str):
                value = Template(templ).substitute(self._macro_values)
            elif isinstance(templ, list):
                value = [Template(tp).substitute(self._macro_values) for tp in templ]
            else:
                raise TypeError(f"Unexpected template type, should be str or stringlist: {templ}")
            widget.setProperty(prop, value)


class MacroEditExtension:
    """
    Adds helpful macro editing options in designer on double or right click.

    See the BasicSettingsExtension from PyDM
    """

    def __init__(self, widget: DesignerWidget):
        self.widget = widget
        self.edit_macros_action = QAction("&Edit Core Properties", self.widget)
        self.edit_macros_action.triggered.connect(self.open_dialog)

    def actions(self) -> list[QAction]:
        """
        PyDM checks this to decide which actions to prepent in designer. The first action is mapped to double-click.
        """
        return [self.edit_macros_action]

    def open_dialog(self):
        dialog = MacroValueEditor(self.widget, parent=None)
        dialog.exec_()


class MacroValueEditor(QDialog):
    """
    Dialog for MacroEditExtension

    See the BasicSettingsEditor from PyDM
    """

    def __init__(self, widget: DesignerWidget, parent: QWidget | None):
        super().__init__(parent)
        self.widget = widget
        self.edit_widgets: dict[str, QLineEdit] = {}
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Widget Core Settings Editor")
        outer_layout = QVBoxLayout()
        outer_layout.setContentsMargins(5, 5, 5, 5)
        outer_layout.setSpacing(5)
        self.setLayout(outer_layout)

        edit_form_layout = QFormLayout()
        outer_layout.addLayout(edit_form_layout)

        for macro_name, value in self.widget._macro_values.items():
            self.edit_widgets[macro_name] = QLineEdit()
            self.edit_widgets[macro_name].setText(value)
            edit_form_layout.addRow(macro_name.lower(), self.edit_widgets[macro_name])

        button_layout = QHBoxLayout()
        outer_layout.addLayout(button_layout)

        self.save_button = QPushButton("&Save")
        self.save_button.setAutoDefault(True)
        self.save_button.setDefault(True)
        self.save_button.clicked.connect(self.save_changes)
        update_button = QPushButton("&Update")
        update_button.clicked.connect(self.save_changes)
        cancel_button = QPushButton("&Cancel")
        cancel_button.clicked.connect(self.cancel_changes)
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(update_button)
        button_layout.addWidget(self.save_button)

    def save_changes(self):
        for macro_name, widget in self.edit_widgets.items():
            self.widget._set_macro(macro_name, widget.text())
        if self.sender() == self.save_button:
            self.accept()

    def cancel_changes(self):
        self.close()
