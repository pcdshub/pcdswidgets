# pcdswidgets
LCLS PyDM Widget Library

## Installation
### Prod
Pick your favorite:

- pip install pcdswidgets
- conda install pcdswidgets

### Dev
pip install -e .


## Adding Widgets
### Adding a Symbol-based Widget
This is how you would add e.g. a pump or valve widget with a custom drawing symbol and some color awareness.

This will require at least some familiarity with Python and with the structure of this module.

Largely: refer back to the existing widgets.

The steps are:

1. Create a new subclass of BaseSymbolIcon in the icons subfolder
   - Define a path
   - Implement draw_icon
2. Create a new subclass of PCDSSymbolBase
   - Include your icon as self.icon
   - Add relevant properties as needed, or inherit them from the existing mixins
   - include the _qt_designer_ class attribute
3. make, to update pyproject.toml with new widget locations

If the widget has been added and is included in the pyproject.toml file, it will appear in designer after installing pcdswidgets.


### Adding a Composite Widget
This is how you would convert a .ui file with macro substitution that is normally used with PyDMEmbeddedDisplay into a designer widget served from here.

This is not required, but you would do this to make your widget globally available and easier to add to screens.

This requires only basic Python knowledge.

The steps are:

1. Create a widget as a PyDM screen
   - Use qt designer to define the layout (saves a .ui file)
   - Use PyDM macros to define user inputs
2. Try it!
   - Use PyDMEmbeddedDisplay to include your widget in other screens
   - Iterate, update the widget until you like it.
3. Bring it here
   - Copy your .ui file in the pcdswidgets/builder/ui folder.
4. make
   - This will create two .py files, one with the layouts and one with some scaffolding for macro conversions.
5. Create a widget class
   - Look around for examples, e.g. pcdswidgets/motion/positioner_widget.py
   - Keeping these in separate files can avoid circular import errors and lets us include widgets inside widgets
   - Import from the _base module created from your .ui file and subclass
6. make, again
   - This will include your widget in pyproject.toml

If the widget has been added and is included in the pyproject.toml file, it will appear in designer after installing pcdswidgets.


#### Widget Classes
The widget class looks something like:
```
from pcdswidgets.builder.ui.my_widget_base import MyWidgetBase


class MyWidget(MyWidgetBase):
    _qt_designer_ = {
        "group": "My Category",
        "is_container": False,
    }
```

If you like, you can extend these classes to add additional python code to use at runtime.


#### Limitations
- Widgets that contain PyDMEmbeddedWidget are not supported: bootstrap these by turning the contents into widgets themselves.
- The automatic type hinting runs into issues when the qt object names are the same as the classnames. If you want to extend the widget class in python, giving your widgets more unique names will help give more useful type hints, automatically.
