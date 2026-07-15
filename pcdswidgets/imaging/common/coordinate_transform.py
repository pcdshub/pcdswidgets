"""Coordinate transformation for PV value recalculation."""

from __future__ import annotations


class CoordinateTransform:
    """Affine transform: forward(v) = v * scale + offset.

    Parameters
    ----------
    scale : float
        Multiplier.
    offset : float
        Additive offset.
    """

    def __init__(self, scale: float = 1.0, offset: float = 0.0):
        self._scale = scale
        self._offset = offset

    @property
    def scale(self) -> float:
        return self._scale

    @property
    def offset(self) -> float:
        return self._offset

    def forward(self, v: float) -> float:
        """Apply transform: v * scale + offset."""
        return v * self._scale + self._offset

    def inverse(self, v: float) -> float:
        """Reverse transform: (v - offset) / scale."""
        if self._scale == 0:
            return v
        return (v - self._offset) / self._scale

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
