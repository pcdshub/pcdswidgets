import inspect
from pathlib import Path

import pytest
from pydm.widgets.embedded_display import PyDMEmbeddedDisplay
from pydm.widgets.related_display_button import PyDMRelatedDisplayButton
from pydm.widgets.shell_command import PyDMShellCommand
from pytestqt.qtbot import QtBot
from qtpy.QtGui import QIcon
from qtpy.QtWidgets import QLabel

from pcdswidgets.builder.designer_options import DesignerOptions
from pcdswidgets.builder.icon_options import IconOptions
from pcdswidgets.generated.tests.builder.widget_for_builder_test_base import WidgetForBuilderTestBase

from .widget_for_builder_test import WidgetForBuilderTest


@pytest.fixture(scope="function")
def test_widget(qtbot: QtBot) -> WidgetForBuilderTest:
    widget = WidgetForBuilderTest()
    qtbot.add_widget(widget)
    return widget


def test_has_expected_hints():
    hints = inspect.get_annotations(WidgetForBuilderTestBase)

    for label_name in ("name_label", "num_label", "name_num_label"):
        assert hints[label_name] == "QLabel"
    assert hints["one_two_shell"] == "PyDMShellCommand"
    assert hints["emb_disp"] == "PyDMEmbeddedDisplay"
    assert hints["rel_disp"] == "PyDMRelatedDisplayButton"


def test_has_expected_widgets(test_widget: WidgetForBuilderTest):
    assert isinstance(test_widget.name_label, QLabel)
    assert isinstance(test_widget.num_label, QLabel)
    assert isinstance(test_widget.name_num_label, QLabel)
    assert isinstance(test_widget.one_two_shell, PyDMShellCommand)
    assert isinstance(test_widget.emb_disp, PyDMEmbeddedDisplay)
    assert isinstance(test_widget.rel_disp, PyDMRelatedDisplayButton)


def test_has_expected_macro_to_widget(test_widget: WidgetForBuilderTest):
    assert set(test_widget._macro_to_widget.keys()) == {"NAME", "NUM", "ONE", "TWO", "EMB_TITLE", "REL_TITLE"}
    assert set(test_widget._macro_to_widget["NAME"]) == {"name_label", "name_num_label"}
    assert set(test_widget._macro_to_widget["NUM"]) == {"num_label", "name_num_label"}
    assert test_widget._macro_to_widget["ONE"] == ["one_two_shell"]
    assert test_widget._macro_to_widget["TWO"] == ["one_two_shell"]
    assert test_widget._macro_to_widget["EMB_TITLE"] == ["emb_disp"]
    assert test_widget._macro_to_widget["REL_TITLE"] == ["rel_disp"]


def test_has_expected_widget_to_macro(test_widget: WidgetForBuilderTest):
    assert set(test_widget._widget_to_macro.keys()) == {
        "name_label",
        "num_label",
        "name_num_label",
        "one_two_shell",
        "emb_disp",
        "rel_disp",
    }
    assert test_widget._widget_to_macro["name_label"] == ["NAME"]
    assert test_widget._widget_to_macro["num_label"] == ["NUM"]
    assert set(test_widget._widget_to_macro["name_num_label"]) == {"NAME", "NUM"}
    assert set(test_widget._widget_to_macro["one_two_shell"]) == {"ONE", "TWO"}
    assert test_widget._widget_to_macro["emb_disp"] == ["EMB_TITLE"]
    assert test_widget._widget_to_macro["rel_disp"] == ["REL_TITLE"]


def test_has_expected_widget_to_pre_template(test_widget: WidgetForBuilderTest):
    assert set(test_widget._widget_to_pre_template.keys()) == {
        "name_label",
        "num_label",
        "name_num_label",
        "one_two_shell",
        "emb_disp",
        "rel_disp",
    }
    assert set(test_widget._widget_to_pre_template["name_label"]) == {("text", "Name: ${NAME}"), ("toolTip", "${NAME}")}
    assert test_widget._widget_to_pre_template["num_label"] == [("text", "Num: ${NUM}")]
    assert test_widget._widget_to_pre_template["name_num_label"] == [("text", "${NAME}:${NUM}")]
    assert test_widget._widget_to_pre_template["one_two_shell"] == [
        ("commands", ["echo ${ONE}", "echo ${TWO}", "echo ${ONE}:${TWO}"])
    ]
    assert test_widget._widget_to_pre_template["emb_disp"] == [("macros", '{"TITLE": "${EMB_TITLE}"}')]
    assert test_widget._widget_to_pre_template["rel_disp"] == [("macros", ['{"TITLE": "${REL_TITLE}"}'])]


def test_has_expected_macro_values(test_widget: WidgetForBuilderTest):
    assert test_widget._macro_values == {
        "NAME": "",
        "NUM": "",
        "ONE": "",
        "TWO": "",
        "EMB_TITLE": "",
        "REL_TITLE": "",
    }


def test_macro_substitution_labels(test_widget: WidgetForBuilderTest):
    assert test_widget.name_label.text() == "Name: ${NAME}"
    assert test_widget.num_label.text() == "Num: ${NUM}"
    assert test_widget.name_num_label.text() == "${NAME}:${NUM}"

    test_widget.setProperty("name", "Jimmy")

    assert test_widget.name_label.text() == "Name: Jimmy"
    assert test_widget.num_label.text() == "Num: ${NUM}"
    assert test_widget.name_num_label.text() == "${NAME}:${NUM}"

    test_widget.setProperty("num", "02")

    assert test_widget.name_label.text() == "Name: Jimmy"
    assert test_widget.num_label.text() == "Num: 02"
    assert test_widget.name_num_label.text() == "Jimmy:02"

    test_widget.setProperty("name", "Steven")

    assert test_widget.name_label.text() == "Name: Steven"
    assert test_widget.num_label.text() == "Num: 02"
    assert test_widget.name_num_label.text() == "Steven:02"


def test_macro_substitution_list_widget(test_widget: WidgetForBuilderTest):
    assert test_widget.one_two_shell.readCommands() == ["echo ${ONE}", "echo ${TWO}", "echo ${ONE}:${TWO}"]

    test_widget.setProperty("one", "UNO")

    assert test_widget.one_two_shell.readCommands() == ["echo ${ONE}", "echo ${TWO}", "echo ${ONE}:${TWO}"]

    test_widget.setProperty("two", "DOS")

    assert test_widget.one_two_shell.readCommands() == ["echo UNO", "echo DOS", "echo UNO:DOS"]

    test_widget.setProperty("one", "ICHI")

    assert test_widget.one_two_shell.readCommands() == ["echo ICHI", "echo DOS", "echo ICHI:DOS"]


def test_macro_substitution_subdisplays(test_widget: WidgetForBuilderTest):
    assert test_widget.emb_disp.readMacros() == '{"TITLE": "${EMB_TITLE}"}'

    test_widget.setProperty("emb_title", "Embedded")

    assert test_widget.emb_disp.readMacros() == '{"TITLE": "Embedded"}'

    assert test_widget.rel_disp.readMacros() == ['{"TITLE": "${REL_TITLE}"}']

    test_widget.setProperty("rel_title", "Related")

    assert test_widget.rel_disp.readMacros() == ['{"TITLE": "Related"}']


def test_filepath_subdisplays(test_widget: WidgetForBuilderTest):
    canonical_path = Path(__file__).parent.resolve() / "subdisplay.ui"
    assert canonical_path.exists()
    assert test_widget.emb_disp.readFilename() == str(canonical_path)
    assert test_widget.rel_disp.readFilenames() == [str(canonical_path)]


def test_no_icon(qtbot: QtBot):
    assert WidgetForBuilderTest.get_designer_icon() is None


def test_iconfont_icon(qtbot: QtBot):
    class TestCls(WidgetForBuilderTest):
        designer_options = DesignerOptions(
            group="ECS Tests Builder",
            is_container=False,
            icon=IconOptions.terminal,
        )

    assert isinstance(TestCls.get_designer_icon(), QIcon)


def test_png_icon(qtbot: QtBot):
    class TestCls(WidgetForBuilderTest):
        designer_options = DesignerOptions(
            group="ECS Tests Builder",
            is_container=False,
            icon="lcls.png",
        )

    assert isinstance(TestCls.get_designer_icon(), QIcon)
