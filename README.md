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
### Widget Sizing
Device control widgets should fall into exactly one of three size classes.
Widgets can be smaller than the maximum of their size class by up to 10% before being flagged by CI.

To ensure sizing consistency, set the minimum and maximum sizes to values that look good throughout the range
and are permissible sizes as recorded below.
It's recommended to used fixed sizing when possible because dynamic sizing is hard to do right.

Widgets should always be maintained to work at the original designed size, because changing this can break existing screens.

#### Full Size
- Width: 250px
- Height: 120px

#### Compact Size
- Width: 75px
- Height: 75px

#### Row Size
- Width: 680px
- Height: 40px

#### Widgets that aren't control widgets (containers, etc.)
These should not have a maximum or a minimum size- they should be usable at any size.

#### Widgets created before 2026
These may have a variety of sizes because we had no standards, and will not be checked in CI.


### Widget Naming
Device control widgets should be named based on the type of device that they control.
The name should be specific enough to distinguish it from other widgets, but general enough to cover all devices that can be used.
Widgets are named using CamelCase and must end with the size, e.g. `MotorRecordFull`

There is no need to end a widget name with "Widget".

Widgets with ui files, such as the composite widgets, should have parity between the ui file name and the widget name, for example `motor_record_full.ui` for `MotorRecordFull`, as well as the module that contains the widget which should be called `motor_record_full.py`.

Widgets should never be renamed between tags, this will break existing screens.

Widgets named before 2026 may break some of these rules because we don't want to rename them.


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
from pcdswidgets.builder.ui.some_name_base import SomeNameBase


class SomeName(SomeNameBase):
    _qt_designer_ = {
        "group": "Some Category",
        "is_container": False,
    }
```

If you like, you can extend these classes to add additional python code to use at runtime.


#### Limitations
- Widgets that contain PyDMEmbeddedWidget are not supported: bootstrap these by turning the contents into widgets themselves.
- The automatic type hinting runs into issues when the qt object names are the same as the classnames. If you want to extend the widget class in python, giving your widgets more unique names will help give more useful type hints, automatically.
