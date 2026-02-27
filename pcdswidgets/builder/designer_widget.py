"""
Helper for using designer to layout widgets.
"""

from string import Template
from typing import ClassVar, Protocol

from qtpy.QtWidgets import QWidget


class _UiForm(Protocol):
    def setupUi(self, Form): ...

    def retranslateUi(self, Form): ...


class DesignerWidget(QWidget):
    """Helper class for converting pydm displays for embedding to standalone widgets."""

    # Loaded from uic
    ui_form: ClassVar[type[_UiForm]]
    # Macro name to widget names that include that macro
    _macro_to_widget: ClassVar[dict[str, list[str]]]
    # Widget name to required macros: all must be non-empty before updating
    _widget_to_macro: ClassVar[dict[str, list[str]]]
    # Widget name to per-property template to fill
    _widget_to_pre_template: ClassVar[dict[str, list[tuple[str, str | list[str]]]]]
    # Current values for each macro
    _macro_values: dict[str, str]

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
