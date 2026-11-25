"""Colours and drawing of pcdswidgets.common.ethercat: one palette, filled into the status stylesheet."""

import re

import pytest

from pcdswidgets.common.ethercat import style
from pcdswidgets.common.ethercat.model import H_DISCONNECTED, H_FAULT, H_OK

HEX = re.compile(r"#[0-9a-fA-F]{6}\b")


def test_stylesheet_template_has_no_colour_of_its_own():
    """Colours come only from style.PALETTE: the .qss template refers to them by name."""
    template = re.sub(r"/\*.*?\*/", "", style.STATUS_QSS.read_text(), flags=re.S)
    assert HEX.findall(template) == []
    assert {"$fault", "$editable", "$muted"} <= set(re.findall(r"\$\w+", template))


def test_stylesheet_gets_the_palette():
    sheet = style.status_stylesheet()
    assert "$" not in sheet
    for name in ("fault", "editable", "muted"):
        assert style.PALETTE[name] in sheet


def test_qt_colours_come_from_the_palette():
    assert style.FAULT_RED.name() == style.PALETTE["fault"]
    assert style.MUTED_GREY.name() == style.PALETTE["muted"]
    assert {k: c.name() for k, c in style.LOCK_COLORS.items()} == {
        "EDITABLE": style.PALETTE["editable"],
        "LOCKED": style.PALETTE["locked"],
        "UNKNOWN": style.PALETTE["unknown"],
    }


@pytest.mark.parametrize("health, colour", [(H_OK, "muted"), (H_FAULT, "fault")])
def test_dot_pixmap_colors(qapp, health, colour):
    image = style.dot_pixmap(health, 12).toImage()
    assert image.pixelColor(6, 6).name() == style.PALETTE[colour]


def test_disconnected_dot_is_hollow(qapp):
    image = style.dot_pixmap(H_DISCONNECTED, 12).toImage()
    assert image.pixelColor(6, 6).alpha() == 0
