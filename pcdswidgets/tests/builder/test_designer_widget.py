import inspect
from pathlib import Path

import pytest
from pydm.widgets.shell_command import PyDMShellCommand
from pytestqt.qtbot import QtBot
from qtpy.QtGui import QIcon
from qtpy.QtWidgets import QLabel

from pcdswidgets.builder.designer_options import DesignerOptions
from pcdswidgets.builder.icon_options import IconOptions
from pcdswidgets.generated.tests.builder.builder_basic_test_widget_base import BuilderBasicTestWidgetBase

from .builder_basic_test_widget import BuilderBasicTestWidget
from .builder_filepath_test_widget import BuilderFilepathTestWidget


@pytest.fixture(scope="function")
def basic_test_widget(qtbot: QtBot) -> BuilderBasicTestWidget:
    widget = BuilderBasicTestWidget()
    qtbot.add_widget(widget)
    return widget


@pytest.fixture(scope="function")
def filepath_test_widget(qtbot: QtBot) -> BuilderFilepathTestWidget:
    widget = BuilderFilepathTestWidget()
    qtbot.add_widget(widget)
    return widget


def test_has_expected_hints():
    hints = inspect.get_annotations(BuilderBasicTestWidgetBase)

    assert hints["Form"] == "QtWidgets.QWidget"
    for label_name in ("name_label", "num_label", "name_num_label"):
        assert hints[label_name] == "QtWidgets.QLabel"
    assert hints["one_two_shell"] == "PyDMShellCommand"


def test_has_expected_widgets(basic_test_widget: BuilderBasicTestWidget):
    assert isinstance(basic_test_widget.name_label, QLabel)
    assert isinstance(basic_test_widget.num_label, QLabel)
    assert isinstance(basic_test_widget.name_num_label, QLabel)
    assert isinstance(basic_test_widget.one_two_shell, PyDMShellCommand)


def test_has_expected_macro_to_widget(basic_test_widget: BuilderBasicTestWidget):
    assert set(basic_test_widget._macro_to_widget.keys()) == {"NAME", "NUM", "ONE", "TWO"}
    assert set(basic_test_widget._macro_to_widget["NAME"]) == {"name_label", "name_num_label"}
    assert set(basic_test_widget._macro_to_widget["NUM"]) == {"num_label", "name_num_label"}
    assert basic_test_widget._macro_to_widget["ONE"] == ["one_two_shell"]
    assert basic_test_widget._macro_to_widget["TWO"] == ["one_two_shell"]


def test_has_expected_widget_to_macro(basic_test_widget: BuilderBasicTestWidget):
    assert set(basic_test_widget._widget_to_macro.keys()) == {
        "name_label",
        "num_label",
        "name_num_label",
        "one_two_shell",
    }
    assert basic_test_widget._widget_to_macro["name_label"] == ["NAME"]
    assert basic_test_widget._widget_to_macro["num_label"] == ["NUM"]
    assert set(basic_test_widget._widget_to_macro["name_num_label"]) == {"NAME", "NUM"}
    assert set(basic_test_widget._widget_to_macro["one_two_shell"]) == {"ONE", "TWO"}


def test_has_expected_widget_to_pre_template(basic_test_widget: BuilderBasicTestWidget):
    assert set(basic_test_widget._widget_to_pre_template.keys()) == {
        "name_label",
        "num_label",
        "name_num_label",
        "one_two_shell",
    }
    assert set(basic_test_widget._widget_to_pre_template["name_label"]) == {
        ("text", "Name: ${NAME}"),
        ("toolTip", "${NAME}"),
    }
    assert basic_test_widget._widget_to_pre_template["num_label"] == [("text", "Num: ${NUM}")]
    assert basic_test_widget._widget_to_pre_template["name_num_label"] == [("text", "${NAME}:${NUM}")]
    assert basic_test_widget._widget_to_pre_template["one_two_shell"] == [
        ("commands", ["echo ${ONE}", "echo ${TWO}", "echo ${ONE}:${TWO}"])
    ]


def test_has_expected_macro_values(basic_test_widget: BuilderBasicTestWidget):
    assert basic_test_widget._macro_values == {
        "NAME": "",
        "NUM": "",
        "ONE": "",
        "TWO": "",
    }


def test_macro_substitution_labels(basic_test_widget: BuilderBasicTestWidget):
    assert basic_test_widget.name_label.text() == "Name: ${NAME}"
    assert basic_test_widget.num_label.text() == "Num: ${NUM}"
    assert basic_test_widget.name_num_label.text() == "${NAME}:${NUM}"

    basic_test_widget.setProperty("name", "Jimmy")

    assert basic_test_widget.name_label.text() == "Name: Jimmy"
    assert basic_test_widget.num_label.text() == "Num: ${NUM}"
    assert basic_test_widget.name_num_label.text() == "${NAME}:${NUM}"

    basic_test_widget.setProperty("num", "02")

    assert basic_test_widget.name_label.text() == "Name: Jimmy"
    assert basic_test_widget.num_label.text() == "Num: 02"
    assert basic_test_widget.name_num_label.text() == "Jimmy:02"

    basic_test_widget.setProperty("name", "Steven")

    assert basic_test_widget.name_label.text() == "Name: Steven"
    assert basic_test_widget.num_label.text() == "Num: 02"
    assert basic_test_widget.name_num_label.text() == "Steven:02"


def test_macro_substitution_list_widget(basic_test_widget: BuilderBasicTestWidget):
    assert basic_test_widget.one_two_shell.readCommands() == ["echo ${ONE}", "echo ${TWO}", "echo ${ONE}:${TWO}"]

    basic_test_widget.setProperty("one", "UNO")

    assert basic_test_widget.one_two_shell.readCommands() == ["echo ${ONE}", "echo ${TWO}", "echo ${ONE}:${TWO}"]

    basic_test_widget.setProperty("two", "DOS")

    assert basic_test_widget.one_two_shell.readCommands() == ["echo UNO", "echo DOS", "echo UNO:DOS"]

    basic_test_widget.setProperty("one", "ICHI")

    assert basic_test_widget.one_two_shell.readCommands() == ["echo ICHI", "echo DOS", "echo ICHI:DOS"]


def test_no_icon(qtbot: QtBot):
    assert BuilderBasicTestWidget.get_designer_icon() is None


def test_iconfont_icon(qtbot: QtBot):
    class TestCls(BuilderBasicTestWidget):
        designer_options = DesignerOptions(
            group="ECS Tests Builder",
            is_container=False,
            icon=IconOptions.terminal,
        )

    assert isinstance(TestCls.get_designer_icon(), QIcon)


def test_png_icon(qtbot: QtBot):
    class TestCls(BuilderBasicTestWidget):
        designer_options = DesignerOptions(
            group="ECS Tests Builder",
            is_container=False,
            icon="lcls.png",
        )

    assert isinstance(TestCls.get_designer_icon(), QIcon)


def test_macro_substitution_subdisplays(filepath_test_widget: BuilderFilepathTestWidget):
    assert filepath_test_widget.emb_disp.readMacros() == '{"TITLE": "${EMB_TITLE}"}'

    filepath_test_widget.setProperty("emb_title", "Embedded")

    assert filepath_test_widget.emb_disp.readMacros() == '{"TITLE": "Embedded"}'

    assert filepath_test_widget.rel_disp.readMacros() == ['{"TITLE": "${REL_TITLE}"}', "", ""]

    filepath_test_widget.setProperty("rel_title", "Related")

    assert filepath_test_widget.rel_disp.readMacros() == ['{"TITLE": "Related"}', "", ""]


def test_filepath_subdisplays(filepath_test_widget: BuilderFilepathTestWidget):
    canonical_path = Path(__file__).parent.resolve() / "subdisplay.ui"
    assert canonical_path.exists()
    assert filepath_test_widget.emb_disp.readFilename() == str(canonical_path)
    assert filepath_test_widget.rel_disp.readFilenames() == [
        str(canonical_path),
        "some/other/rel/path.ui",
        "/wow/abs/path.ui",
    ]
