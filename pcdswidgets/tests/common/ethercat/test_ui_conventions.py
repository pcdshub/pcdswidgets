"""
Static checks of the ethercat .ui files and widget classes against the pcdswidgets
conventions (builder rules, naming, sizes) and the ECS GUI guide (no inline styles,
Sans Serif 11/12, frames, no horizontal scroll bar).
"""

import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

import pcdswidgets
from pcdswidgets.builder.build import get_main_class_name

MODULE = Path(pcdswidgets.__file__).parent
UI_DIR = MODULE / "ui" / "common" / "ethercat"
UI_FILES = sorted(UI_DIR.glob("*.ui"))
PYDM_PROPS = ("channel", "alarmSensitiveContent", "alarmSensitiveBorder", "ecatStatus")


def widgets(ui_path):
    return list(ET.parse(ui_path).getroot().iter("widget"))


def prop(widget, name):
    for p in widget.findall("property"):
        if p.get("name") == name:
            return p
    return None


def test_expected_ui_files():
    assert [p.name for p in UI_FILES] == [
        "ethercat_terminal_state_double_row.ui",
        "ethercat_terminal_states_stretch.ui",
    ]


@pytest.mark.parametrize("ui_path", UI_FILES, ids=lambda p: p.name)
def test_no_inline_stylesheet(ui_path):
    assert [w.get("name") for w in widgets(ui_path) if prop(w, "styleSheet") is not None] == []


@pytest.mark.parametrize("ui_path", UI_FILES, ids=lambda p: p.name)
def test_pydm_properties_have_stdset0(ui_path):
    missing = [
        f"{w.get('name')}.{p.get('name')}"
        for w in widgets(ui_path)
        for p in w.findall("property")
        if p.get("name") in PYDM_PROPS and p.get("stdset") != "0"
    ]
    assert missing == []


@pytest.mark.parametrize("ui_path", UI_FILES, ids=lambda p: p.name)
def test_root_is_macro_free_qwidget_form(ui_path):
    """Builder rule: macros on the root widget crash the generated widget."""
    root = widgets(ui_path)[0]
    assert (root.get("class"), root.get("name")) == ("QWidget", "Form")
    assert not any("${" in (p.findtext("string") or "") for p in root.findall("property"))


@pytest.mark.parametrize("ui_path", UI_FILES, ids=lambda p: p.name)
def test_fonts_are_sans_serif_11_or_12(ui_path):
    bad = []
    for w in widgets(ui_path):
        font = prop(w, "font")
        if font is not None and (font.findtext("font/family"), font.findtext("font/pointsize")) not in (
            ("Sans Serif", "11"),
            ("Sans Serif", "12"),
        ):
            bad.append(w.get("name"))
    assert bad == []


@pytest.mark.parametrize(
    "name, cls",
    [
        ("PyDMLabel_name", "PyDMLabel"),
        ("PyDMLabel_rbv", "PyDMLabel"),
        ("PyDMEnumComboBox_state", "PyDMEnumComboBox"),
    ],
)
def test_terminal_naming_contract(name, cls):
    names = {w.get("name"): w.get("class") for w in widgets(UI_DIR / "ethercat_terminal_state_double_row.ui")}
    assert names.get(name) == cls


def test_states_naming_and_frame():
    ws = {w.get("name"): w for w in widgets(UI_DIR / "ethercat_terminal_states_stretch.ui")}
    assert ws["DeviceName"].get("class") == "PyDMLabel"
    assert ws["terminalWidget"].get("class") == "EthercatTerminalStateDoubleRow"
    assert "PyDMEmbeddedDisplay" not in {w.get("class") for w in ws.values()}  # unsupported in composites
    frame = ws["screenFrame"]
    assert prop(frame, "frameShape").findtext("enum") == "QFrame::Box"
    assert prop(frame, "frameShadow").findtext("enum") == "QFrame::Sunken"
    tree = ws["terminalTree"]
    assert prop(tree, "horizontalScrollBarPolicy").findtext("enum") == "Qt::ScrollBarAlwaysOff"


@pytest.mark.parametrize(
    "ui_name, size",
    [
        ("ethercat_terminal_state_double_row.ui", (800, 100)),  # double row
        ("ethercat_terminal_states_stretch.ui", (850, 1000)),  # docked system summary
    ],
)
def test_design_sizes(ui_name, size):
    rect = prop(widgets(UI_DIR / ui_name)[0], "geometry").find("rect")
    assert (int(rect.findtext("width")), int(rect.findtext("height"))) == size


@pytest.mark.parametrize("ui_path", UI_FILES, ids=lambda p: p.name)
def test_generated_and_main_files_exist(ui_path):
    stem = ui_path.stem
    assert (MODULE / "generated" / "common" / "ethercat" / f"{stem}_form.py").is_file()
    assert (MODULE / "generated" / "common" / "ethercat" / f"{stem}_base.py").is_file()
    main = MODULE / "common" / "ethercat" / f"{stem}.py"
    assert f"class {get_main_class_name(str(ui_path))}(" in main.read_text()


def test_terminal_macros_become_properties():
    from pcdswidgets.common.ethercat.ethercat_terminal_state_double_row import EthercatTerminalStateDoubleRow

    assert set(EthercatTerminalStateDoubleRow._macro_to_widget) == {"PREFIX", "PORT", "TERMINAL_NAME", "TERMINAL_TYPE"}
    for name in ("prefix", "port", "terminal_name", "terminal_type", "confirmRequests"):
        assert hasattr(EthercatTerminalStateDoubleRow, name)


def test_states_designer_properties():
    """In designer the tree widget only asks for plc, prefix, discoveryFile and confirmRequests."""
    from pcdswidgets.common.ethercat.ethercat_terminal_states_stretch import EthercatTerminalStatesStretch

    meta = EthercatTerminalStatesStretch.staticMetaObject
    own = {
        meta.property(i).name(): meta.property(i).isDesignable()
        for i in range(meta.propertyOffset(), meta.propertyCount())
    }
    assert {name for name, designable in own.items() if designable} == {
        "plc",
        "prefix",
        "discoveryFile",
        "confirmRequests",
    }
    assert own["mock"] is False and own["mockOverridesFile"] is False  # code / macros / tests only
    assert "amsNetId" not in own


def test_designer_group():
    from pcdswidgets.common.ethercat.ethercat_terminal_state_double_row import EthercatTerminalStateDoubleRow
    from pcdswidgets.common.ethercat.ethercat_terminal_states_stretch import EthercatTerminalStatesStretch

    for cls in (EthercatTerminalStateDoubleRow, EthercatTerminalStatesStretch):
        assert cls._qt_designer_["group"] == "ECS Common Ethercat"


def test_code_has_no_green_or_inline_colour():
    source = "".join(p.read_text() for p in (MODULE / "common" / "ethercat").glob("*.py"))
    assert "QColor(0, 1" not in source and "rgb(0, 1" not in source  # no green
    assert '.setStyleSheet("color' not in source


def test_status_sheet_only_targets_ecatstatus_and_titles():
    qss = re.sub(r"/\*.*?\*/", "", (MODULE / "common" / "ethercat" / "ethercat_status.qss").read_text(), flags=re.S)
    selectors = [s.strip() for block in re.findall(r"([^{}]+)\{", qss) for s in block.split(",")]
    allowed = ("PyDMLabel#DeviceName", "PyDMLabel#PyDMLabel_name")
    assert selectors and all("ecatStatus" in s or s in allowed for s in selectors), selectors
