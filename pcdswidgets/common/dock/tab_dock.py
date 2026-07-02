"""
Implementation of a tabbed dock widget.

This is more constrained and opinionated than the built-in Qt docking elements,
and it is easier to deploy than the Qt Advanced Docking system, with accordingly less functionality.

This was originally LucidDock from the lucid module,
ported here to have lighter dependencies and to be more generic.
"""

from functools import partial
from typing import Callable, ClassVar

from pydm.utilities import IconFont
from qtpy.QtCore import QPoint, Qt
from qtpy.QtGui import QCursor
from qtpy.QtWidgets import (
    QApplication,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QTabWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

try:
    from qtpy.QtCore import pyqtSignal as Signal
except ImportError:
    from qtpy.QtCore import Signal  # type: ignore


ifont = IconFont()

DOCK_CONTROLS = """
This dock can hold any PyDM screen or qt widget.
You can populate the dock via other widgets, such as dockable buttons.

Buttons that have the anchor mouseover cursor are dockable.

Right click on such a button to bring up an options menu.

The shortcuts are:

- Left click on a dockable button to replace the current tab.
- Ctrl + click to open the screen in a new tab.
- Shift + click to open the screen in a new window.

The arrows have the following behavior:

- Click the up arrow to bring a tab into a new window.
- Click the down arrow to bring a window into a tab.

Screens that are already open will be moved instead of opening a second copy.

For screens that are sourced from a TabDockButton, we will check the source
file for updates when you try to open them in the dock again, otherwise
the screens will be cached.
"""

# Type helpers: some functions here accept fully constructed widgets or functions that produce them later as-needed
DeferredWidget = QWidget | Callable[[], QWidget]
DeferredWidgetList = list[QWidget] | Callable[[], list[QWidget]]
DeferredTitleList = list[str] | Callable[[], list[str]]


class TabDock(QWidget):
    """
    A widget that implements tabbed dock/undock functionality.

    The widget contents of the dock can be changed using a TabDockButton,
    or by implementing other widgets that call the classmethods here.

    It is expected but not enforced that only one TabDock exists at a time.
    If multiple TabDock widgets exist, the most recently created dock is the main dock.

    Most of the functionality is exposed as classmethods so that other code does not have
    to locate the dock singleton, instead you can reference the TabDock class directly.

    You should usually populate the dock by calling TabDock.add_to_dock_user_keybinds,
    which will:
    - Replace the current tab if no modifiers are held
    - Add a new tab if the ctrl modifier key is held
    - Open in a new window if the shift modifier key is held
    - Open in a new window if the dock is not visible

    or TabDock.add_to_dock_user_menu, which does the same but with
    clickable menu options.

    Parameters
    ----------
    parent : QWidget, optional
        Standard qt parent argument
    """

    _qt_designer_ = {
        "group": "ECS Common Dock",
        "is_container": False,
    }

    _instance: ClassVar["TabDock"]

    grid_changed = Signal()

    def __init__(self, parent: QWidget | None = None):
        TabDock._instance = self
        super().__init__(parent)

        self.tab_widgets: list[list[QTabWidget]] = [[]]
        self.detached_widgets: set[QWidget] = set()

        self.fixed_tab_width = 850
        self.dock_cols = 1

        self.attach_buttons: list[QToolButton] = []

        self.settings_button = QToolButton()
        self.settings_button.setIcon(ifont.icon("anchor"))  # type: ignore
        self.settings_button.clicked.connect(self.show_settings)
        self.settings_button.setToolTip("Dock Settings")
        self.settings_widget = None

        first_tabs = self._create_subdock(settings_button=self.settings_button)
        self.tab_widgets[0].append(first_tabs)
        self.set_fixed_tab_width(self.fixed_tab_width)

        self.glayout = QGridLayout()
        self.glayout.addWidget(first_tabs)
        self.setLayout(self.glayout)

        self.dock_columns_spinbox = QSpinBox()
        self.dock_rows_spinbox = QSpinBox()
        self.apply_settings_button = QPushButton("Apply")

    @classmethod
    def _get_instance(cls) -> "TabDock":
        """Return the TabDock instance or raise if there is not one."""
        try:
            return cls._instance
        except AttributeError as exc:
            raise RuntimeError("No TabDock widget exists! Cannot do any dock actions!") from exc

    @classmethod
    def set_fixed_tab_width(cls, width: int):
        """
        Set the width of the individual tab widgets that make up the TabDock widget.

        Every tab widget will have the same width.
        The default tab width is 850, defined in this class's __init__.

        Parameters
        ----------
        width : int
            The width of the tab areas in pixels.
        """
        self = cls._get_instance()
        self.fixed_tab_width = width
        for tab_row in self.tab_widgets:
            for tab_inst in tab_row:
                tab_inst.setFixedWidth(width)
        self.setFixedWidth((width + 9) * self.dock_cols)

    def _create_subdock(self, settings_button: QToolButton | None = None) -> QTabWidget:
        """
        Create a QTabWiget suitable for use as one of the tab docks.

        Parameters
        ----------
        settings_button : QToolButton, optional
            A settings button to add to the corner in addition to the attach button.
            This is currently used to add the dock settings button to the first dock.
        """
        tab_widget = QTabWidget()
        tab_widget.setMovable(True)
        tab_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        tab_widget.currentChanged.connect(partial(self.show_correct_tab_buttons, tab_widget=tab_widget))

        corner_widget = QWidget()
        corner_layout = QHBoxLayout()
        corner_widget.setLayout(corner_layout)
        corner_layout.setContentsMargins(0, 0, 0, 0)

        attach_button = QToolButton()
        attach_button.setIcon(ifont.icon("arrow-down"))  # type: ignore
        attach_button.clicked.connect(partial(self.reattach_user_choice, tab_widget))
        attach_button.setEnabled(False)

        self.attach_buttons.append(attach_button)

        corner_layout.addWidget(attach_button)
        if settings_button is not None:
            corner_layout.addWidget(settings_button)

        tab_widget.setCornerWidget(corner_widget, Qt.Corner.TopRightCorner)
        corner_widget.setMinimumHeight(20)

        return tab_widget

    def show_settings(self):
        """Show dock settings in a pop-up dialog."""
        settings = self._get_settings_widget()
        settings.setParent(self)
        settings.setParent(None)  # type: ignore
        settings.move(QCursor().pos())
        settings.show()

    def _get_settings_widget(self) -> QWidget:
        """Assemble the dock settings pop-up dialog."""
        if self.settings_widget is not None:
            return self.settings_widget

        outer_widget = QWidget()
        outer_widget.setWindowTitle("Dock Settings")
        outer_layout = QVBoxLayout()
        outer_widget.setLayout(outer_layout)

        outer_layout.addWidget(QLabel("Dock Grid Settings"))

        form_widget = QWidget()
        form_layout = QFormLayout()
        form_widget.setLayout(form_layout)
        outer_layout.addWidget(form_widget)

        form_layout.addRow("Dock Columns", self.dock_columns_spinbox)
        form_layout.addRow("Dock Rows", self.dock_rows_spinbox)
        form_layout.addRow("", self.apply_settings_button)

        self.dock_columns_spinbox.setMinimum(1)
        self.dock_columns_spinbox.setMaximum(10)
        self.dock_rows_spinbox.setMinimum(1)
        self.dock_rows_spinbox.setMaximum(10)
        self.apply_settings_button.clicked.connect(self.apply_settings)

        dock_controls_label = QLabel(DOCK_CONTROLS)
        outer_layout.addWidget(dock_controls_label)

        self.settings_widget = outer_widget
        return outer_widget

    def apply_settings(self):
        """Apply settings changes from the dock settings dialog."""
        cols = self.dock_columns_spinbox.value()
        self.dock_cols = cols
        rows = self.dock_rows_spinbox.value()
        while len(self.tab_widgets) < rows:
            self.tab_widgets.append([])
        for row_idx, tab_row in enumerate(self.tab_widgets):
            while len(tab_row) < cols:
                new_tabs = self._create_subdock()
                self.glayout.addWidget(new_tabs, row_idx, len(tab_row))
                tab_row.append(new_tabs)
            for col_idx, tab_inst in enumerate(tab_row):
                tab_inst.setVisible(bool(row_idx < rows and col_idx < cols))
        self.set_fixed_tab_width(self.fixed_tab_width)
        self.grid_changed.emit()

    def show_correct_tab_buttons(self, new_idx: int, tab_widget: QTabWidget):
        """
        Ensure that the undock/close buttons are only visible on the active tab.

        Otherwise, it's really easy to accidentally close/undock tabs when trying to change tabs.

        Parameters
        ----------
        new_idx : int
            The integer of the currently open tab. This is intended be passed by the QTabWidget's
            "currentChanged" signal.
        """
        tab_bar = tab_widget.tabBar()
        for idx in range(tab_widget.count()):
            button = tab_bar.tabButton(idx, tab_bar.ButtonPosition.RightSide)
            if button is None:
                continue
            if idx == new_idx:
                button.show()
            else:
                button.hide()

    def get_open_tab_widget(self) -> QTabWidget:
        """
        Return the first tab widget that is empty and visible.

        If no tab widget is empty and visible, returns the first tab widget.
        """
        for tab_row in self.tab_widgets:
            for tab_inst in tab_row:
                if tab_inst.isVisible() and tab_inst.count() == 0:
                    return tab_inst
        return self.tab_widgets[0][0]

    def has_empty_tab(self) -> bool:
        """Return True if any tab is empty as visible."""
        for tab_row in self.tab_widgets:
            for tab_inst in tab_row:
                if tab_inst.isVisible() and tab_inst.count() == 0:
                    return True
        return False

    @classmethod
    def add_to_dock_user_keybinds(cls, widget: DeferredWidget, title: str = ""):
        """
        Add widgets to the dock, based on the user keypresses.

        This is the first intended way to add widgets from external code.

        This checks the user's modifier keys and opens the widget in the current tab (default),
        a new tab (ctrl), or a new window (shift, or invisible dock) as appropriate.

        Parameters
        ----------
        widget : DeferredWidget
            The widget to use, or a callable to produce the widget right before it is needed.
        title : str
            The title of the tab and/or window.
            If omitted we'll use the widget's windowTitle
        """
        if shift_pressed() or not cls._get_instance().isVisible():
            cls.open_in_new_window(widget=widget, title=title)
        else:
            new_tab = ctrl_pressed()
            cls.add_to_dock(widget=widget, title=title, new_tab=new_tab)

    @classmethod
    def add_to_dock_user_menu(
        cls, widget: DeferredWidget, title: str = "", pos: QPoint | None = None, menu: QMenu | None = None
    ) -> QMenu:
        """
        Add widgets to the dock, with a multiple choice menu.

        This is the second intended way to add widgets from external code.

        Rather than using modifier keys like add_to_dock_user_keybinds, this creates
        a compact menu with each variant as an option.

        Parameters
        ----------
        widget : DeferredWidget
            The widget to use, or a callable to produce the widget right before it is needed.
        title : str, optional
            The title of the tab and/or window.
            If omitted we'll use the widget's windowTitle.
        pos : QPoint, optional
            The position to open the menu at.
            If omitted, we won't open the menu.
        menu : QMenu, optional
            If provided, we'll add actions to this menu rather than create a new menu.
            This is used to include these menus as submenus of other menus.

        Returns
        -------
        menu : QMenu
        """
        self = cls._get_instance()
        if menu is None:
            menu = QMenu()
        self.clean_detached_widgets()
        if self.has_empty_tab():
            replace_tab_action = menu.addAction("Open in Empty Tab")
        else:
            replace_tab_action = menu.addAction("Replace Current Tab")
        replace_tab_action.triggered.connect(partial(cls.add_to_dock, widget=widget, title=title, new_tab=False))
        new_tab_action = menu.addAction("Open in New Tab")
        new_tab_action.triggered.connect(partial(cls.add_to_dock, widget=widget, title=title, new_tab=True))
        new_window_action = menu.addAction("Open in New Window")
        new_window_action.triggered.connect(partial(cls.open_in_new_window, widget=widget, title=title))
        if pos is not None:
            menu.exec_(pos)
        return menu

    @classmethod
    def add_many_to_dock_user_menu(
        cls,
        widget_list: DeferredWidgetList,
        title_list: DeferredTitleList | None = None,
        pos: QPoint | None = None,
        menu: QMenu | None = None,
    ) -> QMenu:
        """
        Add widgets to the dock, with a menu and multiple widgets at once.

        This is the third intended way to add widgets from external code.

        This creates a compact menu where we can either open every widget in a new tab or every widget
        in a new window.

        Parameters
        ----------
        widget_list : DeferredWidgetList
            The widgets to use, or a callable to produce the widgets right before they are needed.
        title_list : DeferredWidgetList, optional
            The title of each tab and/or window, or a callable to produce the titles right before they are needed.
            If omitted we'll use each widget's windowTitle.
        pos : QPoint, optional
            The position to open the menu at.
            If omitted, we won't open the menu.
        menu : QMenu, optional
            If provided, we'll add actions to this menu rather than create a new menu.
            This is used to include these menus as submenus of other menus.

        Returns
        -------
        menu : QMenu
        """
        self = cls._get_instance()
        if menu is None:
            menu = QMenu()
        self.clean_detached_widgets()
        new_tab_action = menu.addAction("Open Each in New Tab")
        new_tab_action.triggered.connect(partial(self.add_to_dock_many, widget_list=widget_list, title_list=title_list))
        new_window_action = menu.addAction("Open Each in New Window")
        new_window_action.triggered.connect(
            partial(self.open_in_new_window_many, widget_list=widget_list, title_list=title_list)
        )
        if pos is not None:
            menu.exec_(pos)
        return menu

    @classmethod
    def add_to_dock(
        cls, widget: DeferredWidget, title: str = "", new_tab: bool = False, tab_widget: QTabWidget | None = None
    ):
        """
        Add a widget to the tabbed docking area.

        This is used internally in TabDock to service the external-facing methods.

        Parameters
        ----------
        widget : DeferredWidget
            The widget to use, or a callable to produce the widget right before it is needed.
        title : str, optional
            The title of the tab and/or window.
            If omitted we'll use the widget's windowTitle.
        new_tab : bool, optional
            If True, opens a new tab for the widget. If False, overwrites the current open tab.
            Defaults to False.
        tab_widget : QTabWidget, optional
            If provided, make sure to put the widget into a specific tabbed docking area.
            Otherwise, we'll find the first open dock, or default to the first dock if all are
            occupied.
        """
        self = cls._get_instance()
        if tab_widget is None:
            tab_widget = self.get_open_tab_widget()
        idx = None
        if not new_tab and tab_widget.count() > 0:
            idx = tab_widget.currentIndex()
            tab_widget.removeTab(idx)

        widget, title = unpack_deferred_widget(widget=widget, title=title)

        # Some typhos screens crash (segfault) when added to the tabs if not shown first (???)
        widget.show()

        if idx is None:
            idx = tab_widget.addTab(widget, title)
        else:
            tab_widget.insertTab(idx, widget, title)

        button_row = QWidget()

        detach_button = QToolButton()
        detach_button.setIcon(ifont.icon("arrow-up"))  # type: ignore
        detach_button.clicked.connect(partial(self.detach_from_dock, tab_widget))
        close_button = QToolButton()
        close_button.setIcon(ifont.icon("window-close"))  # type: ignore
        close_button.clicked.connect(partial(self.close_tab, tab_widget))

        hlayout = QHBoxLayout()
        hlayout.setContentsMargins(3, 0, 0, 0)
        hlayout.addWidget(detach_button)
        hlayout.addWidget(close_button)
        button_row.setLayout(hlayout)

        tab_bar = tab_widget.tabBar()
        tab_bar.setTabButton(idx, tab_bar.ButtonPosition.RightSide, button_row)
        tab_widget.setCurrentIndex(idx)

        try:
            self.detached_widgets.remove(widget)
        except KeyError:
            ...

    @classmethod
    def add_to_dock_many(cls, widget_list: DeferredWidgetList, title_list: DeferredTitleList | None = None):
        """
        Add many widgets to the docking area in new tabs all at once.

        Used in add_many_to_dock_user_menu.

        Parameters
        ----------
        widget_list : DeferredWidgetList
            The widgets to use, or a callable to produce the widgets right before they are needed.
        title_list : DeferredWidgetList, optional
            The title of each tab, or a callable to produce the titles right before they are needed.
            If omitted we'll use each widget's windowTitle.
        """
        widget_list, title_list = unpack_deferred_widget_list(widget_list=widget_list, title_list=title_list)
        for widget, title in zip(widget_list, title_list, strict=True):
            cls.add_to_dock(widget=widget, title=title, new_tab=True)

    def detach_from_dock(self, tab_widget: QTabWidget):
        """
        Move the widget from the currently opened tab into a floating window.

        The tab text will be preserved and moved to the window's title.
        """
        if tab_widget.count() <= 0:
            return
        widget = tab_widget.currentWidget()
        self.open_in_new_window(widget=widget, title=tab_widget.tabText(tab_widget.currentIndex()))

    @classmethod
    def open_in_new_window(cls, widget: DeferredWidget, title: str = ""):
        """
        Move a widget into a floating window and let it be tracked by the dock.

        In contrast with a window opened by a PydmRelatedDisplay widget, this allows the floating window
        to be recalled to the dock at any time.

        Parameters
        ----------
        widget : DeferredWidget
            The widget to use, or a callable to produce the widget right before it is needed.
        title : str, optional
            The title of the tab and/or window.
            If omitted we'll use the widget's windowTitle.
        """
        self = cls._get_instance()
        self.clean_detached_widgets()

        widget, title = unpack_deferred_widget(widget=widget, title=title)

        self.detached_widgets.add(widget)
        widget.setParent(self)
        widget.setParent(None)  # type: ignore
        widget.setWindowTitle(title)
        cursor_pos = QCursor().pos()
        left_of_cursor = QPoint(cursor_pos.x() - 10, cursor_pos.y())
        widget.move(left_of_cursor)
        widget.show()
        widget.activateWindow()
        self.update_attach_enabled()

    @classmethod
    def open_in_new_window_many(cls, widget_list: DeferredWidgetList, title_list: DeferredTitleList | None = None):
        """
        Open many widgets in detached dock mode dialogs all at once.

        Used in add_many_to_dock_user_menu.

        Parameters
        ----------
        widget_list : DeferredWidgetList
            The widgets to use, or a callable to produce the widgets right before they are needed.
        title_list : DeferredWidgetList, optional
            The title of each window, or a callable to produce the titles right before they are needed.
            If omitted we'll use each widget's windowTitle.
        """
        widget_list, title_list = unpack_deferred_widget_list(widget_list=widget_list, title_list=title_list)
        for widget, title in zip(widget_list, title_list, strict=True):
            cls.open_in_new_window(widget=widget, title=title)

    def reattach_user_choice(self, tab_widget: QTabWidget):
        """
        Lets the user select a widget to return to the dock in a new tab.

        If there are no eligible widgets, this does nothing.
        If there is only one eligible widget, this will return that widget to the dock.
        If there are two or more eligible widgets, this will open the attach menu, so the user can pick one widget.

        The window title will be preserved and placed in the tab's text field.
        """
        self.clean_detached_widgets()
        if not self.detached_widgets:
            return
        elif len(self.detached_widgets) == 1:
            widget = list(self.detached_widgets)[0]
            self.reattach_to_dock(widget=widget, tab_widget=tab_widget)
        else:
            self.show_attach_menu(tab_widget=tab_widget, pos=QCursor().pos())

    def reattach_to_dock(self, widget: QWidget, tab_widget: QTabWidget):
        """
        Reattaches a specific widget to the dock in a new tab.

        The window title will be preserved and placed in the tab's text field.

        Parameters
        ----------
        widget : QWidget
            The widget to return to the dock
        """
        self.add_to_dock(title=widget.windowTitle(), widget=widget, new_tab=True, tab_widget=tab_widget)
        try:
            self.detached_widgets.remove(widget)
        except KeyError:
            ...
        self.clean_detached_widgets()

    def show_attach_menu(self, tab_widget: QTabWidget, pos: QPoint | None = None) -> QMenu:
        """
        Create a menu that can be used to reattach one tracked widget to the dock.

        The window title will be preserved and placed in the tab's text field.
        """
        self.clean_detached_widgets()
        menu = QMenu()
        for widget in self.detached_widgets:
            action = menu.addAction(widget.windowTitle())
            action.triggered.connect(partial(self.reattach_to_dock, widget, tab_widget))
        if pos is not None:
            menu.exec_(pos)
        return menu

    def clean_detached_widgets(self):
        """
        Prunes the lists of tracked widgets to remove any windows that the user has closed.

        Closed windows are not eligible to be reattached to the dock.
        """
        for display in list(self.detached_widgets):
            if not display.isVisible():
                self.detached_widgets.remove(display)
        self.update_attach_enabled()

    def update_attach_enabled(self):
        """Enable the attach button if we have any detached widgets, otherwise disables it."""
        for button in self.attach_buttons:
            button.setEnabled(bool(self.detached_widgets))

    def close_tab(self, tab_widget: QTabWidget):
        """Remove the currently opened tab."""
        tab_widget.removeTab(tab_widget.currentIndex())


def unpack_deferred_widget(widget: DeferredWidget, title: str = "") -> tuple[QWidget, str]:
    """
    Resolve a deferred widget to the corresponding widget instance and title for the TabDock.

    Parameters
    ----------
    widget : DeferredWidget
        This should a fully-formed QWidget,
        or a no-arguments callable that produces this widget.
    title : str, optional
        The title to associate with the widget.
        If none is provided, use the widget's window title.

    Returns
    -------
    QWidget, str
        The widget object and title to use in the dock.
    """
    if not isinstance(widget, QWidget):
        widget = widget()
    if not title:
        title = widget.windowTitle()
    return widget, title


def unpack_deferred_widget_list(
    widget_list: DeferredWidgetList, title_list: DeferredTitleList | None
) -> tuple[list[QWidget], list[str]]:
    """
    Resolve deferred widget lists to the corresponding widget instances and titles for the TabDock.

    Parameters
    ----------
    widget_list : DeferredWidgetList
        This should be a fully-formed list of QWidget instances,
        or a no-arguments callable that produces this list.
    title_list : DeferredTitleList, optional
        The list of titles to associate with each widget,
        or a no-arguments callable that produces this list.
        If neither is provided, use each widget's window title.

    Returns
    -------
    list[QWidget], list[str]
        The widget objects and titles to use in the dock.
    """
    if not isinstance(widget_list, list):
        widget_list = widget_list()
    if title_list is None:
        title_list = [widget.windowTitle() for widget in widget_list]
    if not isinstance(title_list, list):
        title_list = title_list()
    return widget_list, title_list


def ctrl_pressed() -> bool:
    """Return True if ctrl key is pressed."""
    return bool(QApplication.keyboardModifiers() & Qt.ControlModifier)


def shift_pressed() -> bool:
    """Return True if shift key is pressed."""
    return bool(QApplication.keyboardModifiers() & Qt.ShiftModifier)
