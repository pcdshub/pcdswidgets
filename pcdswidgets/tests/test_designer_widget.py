import inspect

import pytest
from pytestqt.qtbot import QtBot
from qtpy.QtWidgets import QLabel, QListWidget

from pcdswidgets.builder.ui.pytest_base import PytestBase


class TestWidget(PytestBase): ...


@pytest.fixture(scope="function")
def test_widget(qtbot: QtBot) -> TestWidget:
    widget = TestWidget()
    qtbot.add_widget(widget)
    return widget


def test_has_expected_hints(test_widget: TestWidget):
    class_hints = inspect.get_annotations(TestWidget)
    obj_hints = inspect.get_annotations(test_widget)

    for hints in (class_hints, obj_hints):
        for label_name in ("name_label", "num_label", "name_num_label"):
            assert hints[label_name] is QLabel
        assert hints["one_two_list"] is QListWidget


def test_has_expected_widgets(test_widget: TestWidget):
    assert isinstance(test_widget.name_label, QLabel)
    assert isinstance(test_widget.num_label, QLabel)
    assert isinstance(test_widget.name_num_label, QLabel)
    assert isinstance(test_widget.one_two_list, QListWidget)


def test_has_expected_macro_to_widget(test_widget: TestWidget):
    assert set(test_widget._macro_to_widget.keys()) == {"NAME", "NUM", "ONE", "TWO"}
    assert set(test_widget._macro_to_widget["NAME"]) == {"name_label", "name_num_label"}
    assert set(test_widget._macro_to_widget["NUM"]) == {"num_label", "name_num_label"}
    assert [test_widget._macro_to_widget["ONE"]] == ["one_two_list"]
    assert test_widget._macro_to_widget["TWO"] == ["one_two_list"]


def test_has_expected_widget_to_macro(test_widget: TestWidget):
    assert set(test_widget._widget_to_macro.keys()) == {"name_label", "num_label", "name_num_label", "one_two_list"}
    assert test_widget._widget_to_macro["name_label"] == ["NAME"]
    assert test_widget._widget_to_macro["num_label"] == ["NUM"]
    assert set(test_widget._widget_to_macro["name_num_label"]) == {"NAME", "NUM"}
    assert set(test_widget._widget_to_macro["one_two_list"]) == {"ONE", "TWO"}


def test_has_expected_widget_to_pre_template(test_widget: TestWidget):
    assert set(test_widget._widget_to_pre_template.keys()) == {
        "name_label",
        "num_label",
        "name_num_label",
        "one_two_list",
    }
    assert set(test_widget._widget_to_pre_template["name_label"]) == {("text", "Name: ${NAME}"), ("toolTip", "${NAME}")}
    assert test_widget._widget_to_pre_template["num_label"] == [("text", "Num: ${NUM}")]
    assert test_widget._widget_to_pre_template["name_num_label"] == [("text", "${NAME}:${NUM}")]
    assert test_widget._widget_to_pre_template["one_two_list"] == [
        ("text", ["One: ${ONE}", "Two: ${TWO}", "${ONE}:${TWO}"])
    ]


def test_has_expected_macro_values(test_widget: TestWidget):
    assert test_widget._macro_values == {
        "NAME": "",
        "NUM": "",
        "ONE": "",
        "TWO": "",
    }


def test_macro_substitution_labels(test_widget: TestWidget):
    assert test_widget.name_label.text() == "Name: ${NAME}"
    assert test_widget.num_label.text() == "Num: ${NUM}"
    assert test_widget.name_num_label.text() == "${NAME}:${NUM}"

    test_widget.name = "Jimmy"

    assert test_widget.name_label.text() == "Name: Jimmy"
    assert test_widget.num_label.text() == "Num: ${NUM}"
    assert test_widget.name_num_label.text() == "${NAME}:${NUM}"

    test_widget.num = "02"

    assert test_widget.name_label.text() == "Name: Jimmy"
    assert test_widget.num_label.text() == "Num: 02"
    assert test_widget.name_num_label.text() == "Jimmy:02"

    test_widget.name = "Steven"

    assert test_widget.name_label.text() == "Name: Steven"
    assert test_widget.num_label.text() == "Num: 02"
    assert test_widget.name_num_label.text() == "Steven:02"


def test_macro_substitution_list_widget(test_widget: TestWidget):
    assert test_widget.one_two_list.item(0).text() == "One: ${ONE}"
    assert test_widget.one_two_list.item(1).text() == "Two: ${TWO}"
    assert test_widget.one_two_list.item(2).text() == "${ONE}:${TWO}"

    test_widget.one = "UNO"

    assert test_widget.one_two_list.item(0).text() == "One: ${ONE}"
    assert test_widget.one_two_list.item(1).text() == "Two: ${TWO}"
    assert test_widget.one_two_list.item(2).text() == "${ONE}:${TWO}"

    test_widget.two = "DOS"

    assert test_widget.one_two_list.item(0).text() == "One: UNO"
    assert test_widget.one_two_list.item(1).text() == "Two: DOS"
    assert test_widget.one_two_list.item(2).text() == "UNO:DOS"

    test_widget.one = "ICHI"

    assert test_widget.one_two_list.item(0).text() == "One: ICHI"
    assert test_widget.one_two_list.item(1).text() == "Two: DOS"
    assert test_widget.one_two_list.item(2).text() == "ICHI:DOS"
