from importlib.metadata import entry_points

from pydm.config import ENTRYPOINT_WIDGET

from pcdswidgets.entrypoint_widgets import get_current_widget_table, get_widget_entrypoint_data


def test_toml_has_all_widgets():
    """
    Ensure that all widgets are included in pyproject.toml, and in the generated order.

    If this fails, it's likely that we forgot to run the entrypoint_widgets generator program.
    """
    name_and_entrypoint = get_widget_entrypoint_data()
    current_table, _ = get_current_widget_table()
    for (name, entrypoint), (key, value) in zip(name_and_entrypoint, current_table.items(), strict=True):
        assert name == key
        assert entrypoint == value


def test_entrypoint_has_all_widgets():
    """
    Ensure that all widgets are included in designer via the pydm designer plugin.

    If this fails, but test_toml_has_all_widgets is passing, it's likely because
    pcdswidgets is not installed in dev mode.
    """
    pydm_widgets = entry_points(group=ENTRYPOINT_WIDGET)
    name_and_entrypoint = get_widget_entrypoint_data()
    for name, entrypoint in name_and_entrypoint:
        assert pydm_widgets.select(name=name)[name].value == entrypoint
