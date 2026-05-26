"""
Originally generated from jinja template ui_main_widget.j2

This file can be safely edited to change the runtime behavior of the widget.
"""

import numpy as np
from pydm.widgets import PyDMImageView
from pydm.widgets.colormaps import PyDMColorMap, cmap_names, cmaps
from pyqtgraph import ColorMap
from pyqtgraph.widgets.HistogramLUTWidget import HistogramLUTWidget
from qtpy import QtWidgets

from pcdswidgets.builder.designer_options import DesignerOptions
from pcdswidgets.builder.icon_options import IconOptions
from pcdswidgets.generated.imaging.common.colormap_intesity_control_full_base import ColormapIntesityControlFullBase

_COLORMAP_ORDER = [
    PyDMColorMap.Inferno,
    PyDMColorMap.Hot,
    PyDMColorMap.Magma,
    PyDMColorMap.Plasma,
    PyDMColorMap.Viridis,
    PyDMColorMap.Jet,
    PyDMColorMap.Monochrome,
]


class ColormapIntesityControlFull(ColormapIntesityControlFullBase):
    colormap_combo: QtWidgets.QComboBox
    normalize_check: QtWidgets.QCheckBox
    histogram_container: QtWidgets.QWidget

    designer_options = DesignerOptions(
        group="ECS Imaging Common",
        is_container=False,
        icon=IconOptions.NONE,
    )

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self._image_view: PyDMImageView | None = None

        for cmap_enum in _COLORMAP_ORDER:
            self.colormap_combo.addItem(cmap_names[cmap_enum], cmap_enum)

        # histogram widget for manual intensity control
        layout = QtWidgets.QVBoxLayout(self.histogram_container)
        layout.setContentsMargins(0, 0, 0, 0)
        self._histogram = HistogramLUTWidget(
            parent=self.histogram_container,
            orientation="horizontal",
        )
        layout.addWidget(self._histogram)

        # link callbacks for ui
        self.colormap_combo.currentIndexChanged.connect(self._on_colormap_changed)
        self.normalize_check.toggled.connect(self._on_normalize_toggled)

    def link_image_view(self, image_view: PyDMImageView) -> None:
        """
        Connect this config widget to a PyDMImageView.

        Called by the parent widget at adoption time. Links the histogram
        to the image item and syncs the UI state to current image settings.
        """
        self._image_view = image_view

        # Link histogram to the image's ImageItem for live level control
        self._histogram.setImageItem(image_view.getImageItem())

        # Sync UI to current image view state
        current_cmap = image_view.readColorMap()
        idx = self.colormap_combo.findData(current_cmap)
        if idx >= 0:
            self.colormap_combo.setCurrentIndex(idx)

        self._sync_histogram_gradient(current_cmap)

        self.normalize_check.setChecked(image_view._normalize_data)

        # When histogram levels change, update the image view's colormap limits
        self._histogram.sigLevelChangeFinished.connect(self._on_levels_changed)

    def _sync_histogram_gradient(self, cmap_enum) -> None:
        """Set the histogram gradient to match the given colormap."""
        cm_colors = cmaps[cmap_enum]
        pos = np.linspace(0.0, 1.0, num=len(cm_colors))
        colormap = ColorMap(pos, cm_colors)
        self._histogram.item.gradient.setColorMap(colormap)

    def _on_colormap_changed(self, index: int) -> None:
        if self._image_view is None:
            return
        cmap_enum = self.colormap_combo.itemData(index)
        if cmap_enum is None:
            return
        self._image_view._setColorMap(cmap_enum)
        self._sync_histogram_gradient(cmap_enum)

    def _on_normalize_toggled(self, checked: bool) -> None:
        if self._image_view is None:
            return
        self._image_view._normalize_data = checked

    def _on_levels_changed(self, hist_item) -> None:
        """Update image view min/max when the user drags histogram levels."""
        if self._image_view is None:
            return
        mn, mx = hist_item.getLevels()
        self._image_view.setColorMapLimits(mn, mx)
