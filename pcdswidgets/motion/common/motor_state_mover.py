"""
Originally generated from jinja template ui_main_widget.j2

This file can be safely edited to change the runtime behavior of the widget.
"""

from pathlib import Path

from qtpy.QtCore import QTimer
from qtpy.QtWidgets import QWidget

from pcdswidgets.builder.designer_options import DesignerOptions
from pcdswidgets.builder.icon_options import IconOptions
from pcdswidgets.generated.motion.common.motor_state_mover_base import MotorStateMoverBase
from pcdswidgets.motion.common.state_mover_common import MovingLabel


class MotorStateMover(MotorStateMoverBase):
    designer_options = DesignerOptions(
        group="ECS Motion Common",
        is_container=False,
        icon=IconOptions.NONE,
    )

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        # Resolve the expert screen to an absolute path so the related-display
        # button finds it regardless of where the embedding display lives or
        # whether the screens dir is on PYDM_DISPLAYS_PATH. Mirrors the smaract
        # widgets' approach. The MOTOR macro is forwarded via the button's
        # templated `macros` property (see the .ui).
        expert = Path(__file__).parents[2] / "screens" / "motor_state_mover_expert.py"
        self.expertScreenButton.setFilenames([str(expert)])

        # Swap the static QLabel under the moving LED for a PyDM-managed label
        # so it reliably receives BUSY_RBV updates (a manual PyDMChannel did not
        # deliver values in the running app). Then point it at the same resolved
        # channel the moving LED uses, once the MOTOR macro is substituted in.
        old = self.movingIndicatorLabel
        self.movingIndicatorLabel = MovingLabel(parent=old.parent())
        self.movingIndicatorLabel.setStyleSheet(old.styleSheet())
        self.movingIndicatorLabel.setAlignment(old.alignment())
        self.movingIndicatorLabel.setText(old.text())  # "done" by default
        self.movingIndicatorLabel.alarmSensitiveContent = False
        self.movingIndicatorLabel.alarmSensitiveBorder = False
        self.movingIndicatorLayout.replaceWidget(old, self.movingIndicatorLabel)
        old.deleteLater()

        self._busy_timer = QTimer(parent=self)
        self._busy_timer.setInterval(100)
        self._busy_timer.setSingleShot(True)
        self._busy_timer.timeout.connect(self._setup_moving_label)
        self._busy_timer.start()

    def _setup_moving_label(self) -> None:
        """Point the moving/done label at the same (resolved) channel the moving
        LED uses, once the MOTOR macro has been substituted into it."""
        channel = self.movingIndicator.channel
        if not channel or "${" in channel:
            self._busy_timer.start()
            return
        self.movingIndicatorLabel.channel = channel
