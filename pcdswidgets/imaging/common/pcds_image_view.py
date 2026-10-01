"""
PCDSImageView: a PyDMImageView subclass that reduces camera network traffic.

"""

import logging

from pydm.widgets import PyDMImageView
from qtpy.QtCore import QTimer, Signal

try:
    from qtpy.QtCore import pyqtProperty as Property
except ImportError:  # pragma: no cover
    from qtpy.QtCore import Property  # type: ignore


logger = logging.getLogger(__name__)

_DEFAULT_SLOW_RATE_HZ = 0.5

class PCDSImageView(PyDMImageView):
    """PyDMImageView with visibility-based pausing and a pulsed slow mode.

    Visibility Pausing: owning widget calls pause/resume to stop
    heavy image-stream subscriptions.

    Slow mode: instead of camonitor, a timer "pulses" the
    subscription (connect, grab one frame, disconnect) at ``slowModeRate`` Hz,
    dramatically lowering average network traffic.
    """

    slow_mode_changed = Signal(bool)

    def __init__(self, parent=None, image_channel=None, width_channel=None) -> None:
        self._slow_mode: bool = False
        self._slow_mode_rate: float = _DEFAULT_SLOW_RATE_HZ
        # Start paused: the stream is only established once the owning widget
        # calls resume() (typically on its first showEvent). This prevents
        # background tabs/docks -- which never receive a showEvent -- from
        # quietly running a full-rate camonitor.
        self._paused: bool = True
        self._stream_connected: bool = False
        self._awaiting_frame: bool = False
        self._pulse_timer: QTimer | None = None

        super().__init__(parent=parent, image_channel=image_channel, width_channel=width_channel)

        # connect "slow mode" timer
        self._pulse_timer = QTimer(self)
        self._pulse_timer.timeout.connect(self._open_pulse)


    def _set_stream_connected(self, connected: bool) -> None:
        """Connect or disconnect the heavy image-stream channels (idempotent)."""
        if connected == self._stream_connected:
            return
        for channel in (self._imagechannel, self._widthchannel):
            if channel is None:
                continue
            try:
                channel.connect() if connected else channel.disconnect()
            except Exception:
                logger.exception("Failed to %s stream channel", "connect" if connected else "disconnect")
        self._stream_connected = connected

    def _apply_stream_state(self) -> None:
        """Drive the stream to match the current paused / slow_mode flags.

        Single source of truth: every entry point (pause/resume, slow-mode
        toggle, channel setters) just updates a flag and calls this.
        """
        if self._paused:
            self._stop_pulsing()
            self._set_stream_connected(False)
        elif self._slow_mode:
            self._start_pulsing()
        else:  # live: continuous monitor
            self._stop_pulsing()
            self._set_stream_connected(True)

    # -- Slow Mode -----------------------------------------

    def _apply_pulse_interval(self) -> None:
        if self._pulse_timer is None:
            return
        rate = self._slow_mode_rate if self._slow_mode_rate > 0 else _DEFAULT_SLOW_RATE_HZ
        self._pulse_timer.setInterval(int(1000.0 / rate))

    def _start_pulsing(self) -> None:
        """Begin the repeating connect/grab/disconnect cadence."""
        if self._pulse_timer is None:
            return
        self._apply_pulse_interval()
        self._pulse_timer.start()
        self._open_pulse()  # fetch an initial frame right away

    def _stop_pulsing(self) -> None:
        """Halt the repeating cadence."""
        if self._pulse_timer is not None:
            self._pulse_timer.stop()
        self._awaiting_frame = False

    def _open_pulse(self) -> None:
        """Open the subscription and wait for a single frame."""
        self._awaiting_frame = True
        self._set_stream_connected(True)

    def _close_pulse(self) -> None:
        """Render the frame we just received, then drop the subscription."""
        if self._paused or not self._slow_mode:
            # Mode changed while the frame was in flight; leave the stream as
            # the new mode set it instead of disconnecting.
            return
        # Kick off a redraw of the frame manually since
        # redraw timer is paused when channel is disconnected
        self.needs_redraw = True
        self.redrawImage()
        self._set_stream_connected(False)

    def pause(self) -> None:
        """Tear down the image stream (called when the view is hidden)."""
        self._paused = True
        self._apply_stream_state()

    def resume(self) -> None:
        """Restore the image stream in the current mode (live or slow)."""
        self._paused = False
        self._apply_stream_state()

    # -- Overrides --------------------------------------------------------

    def image_value_changed(self, new_image) -> None:
        super().image_value_changed(new_image)
        if self._awaiting_frame:
            self._awaiting_frame = False
            # Let the current event-loop iteration finish, then render + drop.
            QTimer.singleShot(0, self._close_pulse)

    def setImageChannel(self, value) -> None:
        super().setImageChannel(value)
        self._stream_connected = True  # super() just established a connection
        self._apply_stream_state()

    def setWidthChannel(self, value) -> None:
        super().setWidthChannel(value)
        self._stream_connected = True  # super() just established a connection
        self._apply_stream_state()

    # -- Qt properties ----------------------------------------------------

    def get_slow_mode(self) -> bool:
        return self._slow_mode

    def set_slow_mode(self, enabled: bool) -> None:
        if enabled == self._slow_mode:
            return
        self._slow_mode = enabled
        self._apply_stream_state()
        self.slow_mode_changed.emit(enabled)

    slow_mode = Property(bool, get_slow_mode, set_slow_mode)

    def get_slow_mode_rate(self) -> float:
        return self._slow_mode_rate

    def set_slow_mode_rate(self, rate: float) -> None:
        rate = float(rate)
        if rate <= 0:
            return
        self._slow_mode_rate = rate
        self._apply_pulse_interval()

    slow_mode_rate = Property(float, get_slow_mode_rate, set_slow_mode_rate)
