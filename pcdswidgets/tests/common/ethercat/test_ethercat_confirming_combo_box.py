"""ConfirmingEnumComboBox: a PyDMEnumComboBox that writes only what its confirm hook accepts."""

import pytest

from pcdswidgets.common.ethercat.confirming_combo_box import ConfirmingEnumComboBox
from pcdswidgets.common.ethercat.constants import STATE_ENUM


@pytest.fixture
def combo(qtbot):
    """A combo box showing STATE_ENUM, last value SAFEOP (3); its writes are recorded."""
    box = ConfirmingEnumComboBox()
    qtbot.addWidget(box)
    box.enum_strings_changed(STATE_ENUM)
    box.value_changed(3)
    box.writes = []
    box.send_value_signal[int].connect(box.writes.append)
    return box


def pick(box, text):
    index = box.findText(text)
    box.setCurrentIndex(index)
    box.activated[int].emit(index)  # what a user's choice does
    return index


def test_without_hook_it_writes_like_pydm(combo):
    assert pick(combo, "OP") == 4
    assert combo.writes == [4]


def test_accepted_choice_is_written(combo):
    asked = []
    combo.confirm = lambda index: asked.append(index) or True
    pick(combo, "PREOP")
    assert asked == [1] and combo.writes == [1]


def test_refused_choice_reverts_to_the_last_value(combo):
    combo.confirm = lambda index: False
    pick(combo, "OP")
    assert combo.writes == []
    assert combo.currentText() == "SAFEOP"
