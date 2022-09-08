import pytest
from qtpy.QtWidgets import QWidget

from pcdswidgets.vacuum.base import PCDSSymbolBase
from pcdswidgets.vacuum.mixins import (ErrorMixin, InterlockMixin,
                                       OpenCloseStateMixin, StateMixin)


class PCDSSymbolWithIcon(PCDSSymbolBase):
    """Base mixable class"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.icon = QWidget(parent=self)


class Interlock(InterlockMixin, PCDSSymbolWithIcon):
    """Simplest Interlock Widget"""
    pass


class Error(ErrorMixin, PCDSSymbolWithIcon):
    """Simplest Error Widget"""
    pass


class State(StateMixin, PCDSSymbolWithIcon):
    """Simplest State Widget"""
    pass


class OpenClose(OpenCloseStateMixin, PCDSSymbolWithIcon):
    """Simplest OpenCloseState Widget"""
    pass


@pytest.fixture(scope='function')
def interlock(qtbot):
    inter = Interlock(':ILK')
    qtbot.addWidget(inter)
    inter.create_channels()
    return inter


@pytest.fixture(scope='function')
def error(qtbot):
    error = Error(':ILK')
    qtbot.addWidget(error)
    error.create_channels()
    error.error_enum_changed(('Bad', 'Good'))
    return error


@pytest.fixture(scope='function')
def state(qtbot):
    state = State(':Status')
    qtbot.addWidget(state)
    state.create_channels()
    state.state_enum_changed(('Bad', 'Good'))
    return state


@pytest.fixture(scope='function')
def openclose(qtbot):
    openclose = OpenClose(':Open', 'Close')
    qtbot.addWidget(openclose)
    openclose.create_channels()
    return openclose


@pytest.mark.parametrize('interlock_bit',
                         (0, 1),
                         ids=('low', 'high'))
def test_interlock_value_changed(interlock, interlock_bit):
    interlock.interlock_value_changed(not interlock_bit)
    orig_tooltip = interlock.status_tooltip()
    interlock.interlock_value_changed(interlock_bit)
    interlocked = not bool(interlock_bit)
    assert interlock.interlocked == interlocked
    assert interlock.controls_frame.isEnabled() != interlocked
    assert interlock.status_tooltip() != orig_tooltip


def test_error_value_changed(error):
    orig_tooltip = error.status_tooltip()
    error.error_value_changed(1)
    error.error == 'Good'
    assert orig_tooltip != error.status_tooltip()


def test_state_value_changed(state):
    orig_tooltip = state.status_tooltip()
    state.state_value_changed(1)
    state.state == 'Good'
    assert orig_tooltip != state.status_tooltip()


@pytest.mark.parametrize('open_switch,closed_switch,state',
                         [(1, 1, 'INVALID'), (1, 0, 'Open'),
                          (0, 1, 'Close'), (0, 0, 'INVALID')],
                         ids=['Fault', 'Open', 'Closed', 'Invalid'])
def test_openclose_value_changed(openclose, open_switch, closed_switch, state):
    openclose.state_value_changed('OPEN', open_switch)
    openclose.state_value_changed('CLOSE', closed_switch)
    assert openclose.state == state
