# pcdswidgets
LCLS PyDM Widget Library

## Installation
### Prod
Pick your favorite:

- pip install pcdswidgets
- conda install pcdswidgets

### Dev
A helper script is included here: `build_local_venv.sh` (or, `make venv`).

This will create a `.venv` virtual environment that will be ready to go
to help you run designer and test your custom widgets.
To work, this requires a suitable base environment to already exist on
your system: one with pyqt and designer python plugin support,
which I've found to be tricky to set up in a scripted way in recent years.

These base environments are stored centrally at LCLS and are
specified in `base_env_vars.sh`.

You can run the `build_local_venv.sh` again (or, `make venv`)
to update the environment with any new widgets you've added since the last run.

Once this environment is created, you can use `try_in_designer.sh` to
make sure your widgets are exporting cleanly in an editable way in designer.

You can also use `try_in_pydm.sh` to launch a version of `pydm` that includes
your new widgets.

You can alternatively build your own environment:

- pip install -e .

or

- uv sync

Or whatever your favorite method is.

Note that we can currently only run designer with custom widgets on our Rocky9 OS machines at LCLS.
This is due to complications in build process.


## Adding Widgets
### Widget Sizing
Device control widgets should fall into exactly one of three size classes.
Widgets can be smaller than the maximum of their size class by up to 20% before being flagged by CI.

To ensure sizing consistency, set the minimum and maximum sizes to values that look good throughout the range
and are permissible sizes as recorded below.
It's recommended to used fixed sizing when possible because dynamic sizing is hard to do right.

Widgets should always be maintained to work at the original designed size, because changing this can break existing screens.

#### Full Size
- Width: 400px
- Height: 125px

#### Compact Size
- Width: 100px
- Height: 75px

#### Row Size
- Width: 800px
- Height: 50px

Rows are also allowed to be double-height, e.g. 100px height.

#### Widgets that aren't control widgets (containers, etc.)
These should not have a maximum or a minimum size- they should be usable at any size.

#### Widgets created before 2026
These may have a variety of sizes because we had no standards, and will not be checked in CI.


### Widget Naming
Widget names should contain three parts:

- Type of device controlled
- Descriptor word to differentiate this widget from other possible widgets with the same device type and size
- Size class signifier

Other guidelines:

- The name should not be unnecessarily long, but avoid abbreviations.
- The name should use CamelCase to match qt and python class naming conventions.

  - For example, the first widget added in 2026 was `MotorClassicFull`, because it controls generic epics record motors, is inspired by the classic EDM style, and has the full size class.

- If multiple devices are controlled, include them in order of importance, e.g. `MotorTcClassicRow`.
- There is no need to end a widget name with "Widget". Please avoid this.
- Widgets with ui files, such as the composite widgets, should have parity between the ui file name and the widget name, for example `motor_classic_full.ui` for `MotorClassicFull`.
- Widgets should never be renamed between tags, this will break existing screens.
- Widgets named before 2026 may break some of these rules because we don't want to rename them.


### Adding a Symbol-based Vacuum Widget
This is how you would add e.g. a pump or valve widget with a custom drawing symbol and some color awareness.

This will require at least some familiarity with `Python`, `Qt`, `PyQt`, `pydm`, and with the structure of this module.

Largely: refer back to the existing widgets.

The steps are:

1. Create a new subclass of `BaseSymbolIcon` in the icons subfolder
   - Define a path
   - Implement draw_icon
2. Create a new subclass of `PCDSSymbolBase`
   - Include your icon as self.icon
   - Add relevant properties as needed, or inherit them from the existing mixins
   - include the `_qt_designer_` class attribute
3. `make`, to update `pyproject.toml` and the venv with new widget locations

If the widget has been added and is included in the `pyproject.toml` file, it will appear in designer after installing pcdswidgets.


### Adding a Composite Widget
This is how you would convert a .ui file with macro substitution that is normally used with `PyDMEmbeddedDisplay` into a designer widget served from here.

Note that we can currently only run designer with custom widgets on our Rocky9 OS machines at LCLS!

This is not required, but you would do this to make your widget globally available, trivially discoverable, and easier to add to screens.
The alternative is to pass your widget around via filepath in `PyDMEmbeddedDisplay`, which works but doesn't have the above advantages.

This requires basic `python` knowledge as well as familiarity with making `pydm` displays.

Here are some supplemental pages from the official `pydm` docs that you should understand before adding a widget:

- [PyDM Macro Substitution](https://slaclab.github.io/pydm/tutorials/intro/macros.html)
- [Creating a small (widget) ui file with macros](https://slaclab.github.io/pydm/tutorials/action/designer_inline.html)
- [Creating a screen that uses embedded displays](https://slaclab.github.io/pydm/tutorials/action/designer_main.html)

The steps for creating a new widget are:

1. Create a widget as a PyDM screen
   - Use qt `designer` to define the layout (saves a .ui file)
   - Use `PyDM` macros to define user inputs
2. Try it!
   - Use `PyDMEmbeddedDisplay` to include your widget in other screens
   - Iterate, update the widget until you like it.
3. Bring it here
   - Create a directory under ui, if needed, or use a suitable existing directory: the form must be `pcdswidgets/ui/$subsystem/$type`
   - Examples of subsystem: motion, vacuum
   - Examples of type: common, smaract, beckhoff
   - Pick a name for the ui file following the widget naming rules above
   - Copy in your .ui file to the correct folder with the new name
4. `make`
   - This should have created two python files in `generated`, which are not to be edited by hand.
   - It also creates a python file in `pcdswidgets/$subsystem/$type` which can be edited by hand if you'd like to.
   - It will also create some number of `__init__.py` files to make the generated filetrees valid Python modules.
5. Try it out
   - Run `./try_in_designer.sh` and make a test screen. (Which, reminder: only works on rocky9 at LCLS)
   - After you've made a test screen, then do `./try_in_pydm.sh my_screen.ui` for further testing.
6. Pick an icon (optional)
   - You can select an icon for your widget to use in designer. See the sections below about designer settings and icons.
7. Make a PR!
   - Commit
   - Take some screenshots (in designer, and in pydm)

Some notes:

- If you edit the ui file, you should `make` again, or your changes will not take effect.
- If you change your mind about which subsystem and type directory you'd like to use, you must manually delete the generated files from the old location.


#### Widget Classes
The widget classes look something like:
```
class MyClassFull(MyClassFullBase):
    designer_options = DesignerOptions(
        group="ECS Subsystem Type",
        is_container=False,
        icon=IconOptions.NONE,
    )
```

If you like, you can extend these classes to add additional python code to use at runtime.

#### Icons
If you want to set a non-default icon for the designer widget list,
there are a bunch of standard icons distributed by pydm that are accessible using the IconOptions enum.
Set this in the `icon` option of `DesignerOptions`.

```
    designer_options = DesignerOptions(
        group="ECS Subsystem Type",
        is_container=False,
        icon=IconOptions.expand_arrows_alt,
    )
```

We'll convert these enums to a `QIcon` using `Pydm`'s `IconFont`.
This uses a portable version of `fontawesome`, try running `show_icon_options.sh`
to see all of the icons rendered in a grid.

If you want to make your own icon, you can create a custom `QIcon` using any method you wish
and include it as the `icon` option here.


#### Limitations
- Widgets that contain `PyDMEmbeddedWidget` are not supported: bootstrap these by turning the contents into widgets themselves.
- The automatic type hinting runs into issues when the qt object names are the same as the classnames. If you want to extend the composite widget class in python, giving your child widgets more unique names will result in more useful type hints, automatically.
- Only direct QString and QStringList properties are supported. We still need to implement support for item-based QString widgets such as QListWidget.
- The ordering of the designer widget categories is chaotic. This will require an update to PyDM to resolve.
- In pydm, you can edit a ui file by hand and add a macro anywhere. This is not supported for composite widgets.
