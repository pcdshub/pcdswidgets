"""Coordinate transformation with optional PyDM channel-backed PV tracking.

Provides a chainable affine transform pipeline that can subscribe to EPICS PVs
via PyDMChannel for live offset/scale updates. Used by CamROI and CamMarker to
map between sensor (spinbox/EPICS) coordinates and on-screen pixel coordinates.
"""

from __future__ import annotations

import logging

from pydm.widgets.channel import PyDMChannel
from qtpy.QtCore import QObject, Signal

logger = logging.getLogger(__name__)


class CoordinateTransform(QObject):
    """Affine transform: forward(v) = v * scale + offset, with optional PV backing.

    When ``offset_pv`` or ``scale_pv`` are provided (non-empty strings), a
    PyDMChannel is created to reactively track the live value of that PV.
    Empty string or None means a static default (offset=0, scale=1).

    When ``negate_offset`` is True, the PV value is negated before use as offset.
    When ``invert_scale`` is True, the PV value is inverted (1/val) before use as scale.
    This supports the common pattern: screen = (sensor - start) / bin, where the
    PVs provide "start" and "bin" directly.

    Multiple transforms can be composed via ``stages``: forward() applies self
    first, then each stage in order. inverse() reverses the pipeline.

    Parameters
    ----------
    scale : float
        Static scale multiplier (used when scale_pv is not set).
    offset : float
        Static offset (used when offset_pv is not set).
    scale_pv : str | None
        PV address for live scale updates (e.g. "ca://PREFIX:BinX_RBV").
    offset_pv : str | None
        PV address for live offset updates (e.g. "ca://PREFIX:MinX_RBV").
    negate_offset : bool
        If True, negate the PV value before using as offset.
    invert_scale : bool
        If True, invert the PV value (1/val) before using as scale.
    stages : list[CoordinateTransform] | None
        Downstream transform stages applied after self.
    parent : QObject | None
        Qt parent.
    """

    values_changed = Signal()

    def __init__(
        self,
        scale: float = 1.0,
        offset: float = 0.0,
        scale_pv: str | None = None,
        offset_pv: str | None = None,
        negate_offset: bool = False,
        invert_scale: bool = False,
        stages: list[CoordinateTransform] | None = None,
        parent: QObject | None = None,
    ):
        super().__init__(parent)
        self._scale = scale
        self._offset = offset
        self._negate_offset = negate_offset
        self._invert_scale = invert_scale

        # PV channel state
        self._scale_pv_addr = scale_pv or ""
        self._offset_pv_addr = offset_pv or ""
        self._scale_channel: PyDMChannel | None = None
        self._offset_channel: PyDMChannel | None = None
        self._scale_received = not bool(self._scale_pv_addr)
        self._offset_received = not bool(self._offset_pv_addr)

        # Pipeline stages
        self._stages: list[CoordinateTransform] = stages or []
        for stage in self._stages:
            stage.values_changed.connect(self._on_stage_changed)

    # ── Properties ────────────────────────────────────────────────────────

    @property
    def scale(self) -> float:
        return self._scale

    @property
    def offset(self) -> float:
        return self._offset

    @property
    def stages(self) -> list[CoordinateTransform]:
        return self._stages

    @property
    def ready(self) -> bool:
        """True when all PV-backed levels have received at least one value."""
        if not (self._scale_received and self._offset_received):
            return False
        return all(s.ready for s in self._stages)

    # ── Transform math ────────────────────────────────────────────────────

    def forward(self, v: float) -> float:
        """Apply full pipeline forward: self then stages in order."""
        result = v * self._scale + self._offset
        for stage in self._stages:
            result = stage.forward(result)
        return result

    def inverse(self, v: float) -> float:
        """Reverse full pipeline: stages reversed, then self."""
        result = v
        for stage in reversed(self._stages):
            result = stage.inverse(result)
        if self._scale == 0:
            return result
        return (result - self._offset) / self._scale

    @property
    def effective_scale(self) -> float:
        """Net scale across the full pipeline (for sizing transforms)."""
        s = self._scale
        for stage in self._stages:
            s *= stage.effective_scale
        return s

    # ── PyDMChannel lifecycle ─────────────────────────────────────────────

    def connect(self) -> None:
        """Create and connect PyDMChannels for any configured PV addresses."""
        if self._scale_pv_addr and self._scale_channel is None:
            self._scale_channel = PyDMChannel(
                address=self._scale_pv_addr,
                value_slot=self._on_scale_value,
            )
            self._scale_channel.connect()

        if self._offset_pv_addr and self._offset_channel is None:
            self._offset_channel = PyDMChannel(
                address=self._offset_pv_addr,
                value_slot=self._on_offset_value,
            )
            self._offset_channel.connect()

        for stage in self._stages:
            stage.connect()

    def disconnect(self) -> None:
        """Disconnect and release all PyDMChannels."""
        if self._scale_channel is not None:
            self._scale_channel.disconnect()
            self._scale_channel = None

        if self._offset_channel is not None:
            self._offset_channel.disconnect()
            self._offset_channel = None

        for stage in self._stages:
            stage.disconnect()

    # ── PV value slots ────────────────────────────────────────────────────

    def _on_scale_value(self, value) -> None:
        try:
            raw = float(value)
        except (TypeError, ValueError):
            return
        if raw == 0:
            raw = 1.0
        new_scale = (1.0 / raw) if self._invert_scale else raw
        changed = new_scale != self._scale
        self._scale = new_scale
        self._scale_received = True
        if changed:
            self.values_changed.emit()

    def _on_offset_value(self, value) -> None:
        try:
            raw = float(value)
        except (TypeError, ValueError):
            return
        new_offset = -raw if self._negate_offset else raw
        changed = new_offset != self._offset
        self._offset = new_offset
        self._offset_received = True
        if changed:
            self.values_changed.emit()

    def _on_stage_changed(self) -> None:
        self.values_changed.emit()

    # ── Factory methods (PV-free, for ephemeral transforms) ───────────────

    @classmethod
    def from_bin_change(cls, old_bin: float, new_bin: float) -> CoordinateTransform:
        """Transform for rescaling dependent PVs after a bin change."""
        if new_bin == 0:
            return cls(scale=1.0, offset=0.0)
        return cls(scale=old_bin / new_bin, offset=0.0)

    @classmethod
    def from_offset_change(cls, delta: float) -> CoordinateTransform:
        """Transform for propagating a position offset to dependent PVs."""
        return cls(scale=1.0, offset=delta)
