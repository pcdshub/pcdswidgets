"""
Collapsible widget wrapper for sidebar panels.
"""

import logging

from qtpy.QtCore import Qt
from qtpy.QtGui import QFont
from qtpy.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)

class CollapsibleSection(QWidget):
    """
    A collapsible panel with a clickable title bar.

    The header shows a triangle arrow and a bold title.  Clicking the
    header toggles the content area between visible and hidden.

    """

    def __init__(
        self,
        content: QWidget,
        title: str = None,
        parent: QWidget | None = None,
        *,
        collapsed: bool = True,
    ):
        super().__init__(parent)
        if title is None:
            title = self._infer_title(content)
        self._title_text = title
        self._collapsed = collapsed
        self._build_ui(content)
        self._apply_collapsed_state()

    @staticmethod
    def _infer_title(content: QWidget) -> str:
        """Extract a display title from a widget."""
        # Prefer title_label text if present
        title_lbl = getattr(content, "title_label", None)
        if isinstance(title_lbl, QLabel) and title_lbl.text():
            return title_lbl.text()
        # Fall back to class name
        return type(content).__name__

    def _build_ui(self, content: QWidget) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Header bar
        self._header = QFrame(self)
        self._header.setFrameShape(QFrame.StyledPanel)
        self._header.setStyleSheet(
            "QFrame { background: palette(midlight); "
            "border: 1px solid palette(mid); border-radius: 2px; }"
        )
        self._header.setCursor(Qt.PointingHandCursor)
        header_layout = QHBoxLayout(self._header)
        header_layout.setContentsMargins(4, 2, 4, 2)
        header_layout.setSpacing(4)

        self._arrow = QToolButton(self._header)
        self._arrow.setStyleSheet(
            "QToolButton { border: none; background: transparent; }"
        )
        self._arrow.setArrowType(Qt.RightArrow)
        self._arrow.setFixedSize(16, 16)
        self._arrow.setCheckable(True)
        self._arrow.clicked.connect(self.toggle)
        header_layout.addWidget(self._arrow)

        self._title_label = QLabel(self._title_text, self._header)
        font = QFont()
        font.setBold(True)
        font.setPointSize(9)
        self._title_label.setFont(font)
        self._title_label.setStyleSheet("background: transparent; border: none;")
        header_layout.addWidget(self._title_label)
        header_layout.addStretch()

        outer.addWidget(self._header)

        # Content area
        self._content = QWidget(self)
        self._content.setObjectName("collapsible_content")
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(0, 2, 0, 0)
        self._content_layout.setSpacing(0)
        outer.addWidget(self._content)

        self._content_layout.addWidget(content)
        # Make header clickable (the whole bar, not just the button)
        self._header.mousePressEvent = lambda _ev: self.toggle()

    def toggle(self) -> None:
        """Toggle between collapsed and expanded."""
        self._collapsed = not self._collapsed
        self._apply_collapsed_state()

    def _apply_collapsed_state(self) -> None:
        self._content.setVisible(not self._collapsed)
        self._arrow.setArrowType(
            Qt.DownArrow if not self._collapsed else Qt.RightArrow
        )
        self._arrow.setChecked(not self._collapsed)
        # Let parent layout know our size changed
        self.updateGeometry()
