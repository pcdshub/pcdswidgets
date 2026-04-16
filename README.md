# pcdswidgets
## Usage
This is a widget library that uses the `pydm` framework to add additional widgets to the `pydm` ecosystem.

When `pcdswidgets` is installed in a `python` environment, it will provide:

- Additional widgets in designer via `pydm`'s widget entrypoint.
- The same additional widgets at runtime for use in `pydm` and `PyQt` displays.

At `LCLS`, this is currently distributed as part of the `pcds_conda` environments:

```
source pcds_conda
designer
```

Note that for the designer integration to work properly, the python designer plugin must be built and installed correctly.


## Installation
### Production Environments
`pcdswidgets` is packaged using standard tools and can be installed with standard tools. We maintain both `PyPI` and `conda-forge` builds.

Pick your favorite:

- `pip install pcdswidgets`
- `conda install pcdswidgets`

You can also install `pcdswidgets` using other standard tools (such as `uv`) or directly from source in `GitHub`.


### Development Environments
A helper script is included here: `build_local_venv.sh` (or, `make venv`) (or, just `make`).

This will create a virtual environment under the `.venv` folder that will be ready to go
to help you run designer and test your custom widgets.
To work, this requires a suitable base environment to already exist on
your system: one with PyQt and designer python plugin support,
which is tricky to set up properly.

These base environments are stored centrally at LCLS and are
specified in `base_env_vars.sh`.
If you are not at LCLS, you will need to edit this file to use these scripts.

You can run the `build_local_venv.sh` again (or, `make venv`)
to update the environment with any new widgets you've added since the last run.

Once this environment is created, you can use `try_in_designer.sh` to
make sure your widgets are exporting cleanly in an editable way in designer.

You can also use `try_in_pydm.sh` to launch a version of `pydm` that includes
your new widgets.

You can alternatively build your own environment:

- `pip install -e .`

or

- `uv sync`

or whatever your favorite method is.

Note that we can currently only run designer with custom widgets on our Rocky 9 OS machines at LCLS.
This is due to complications in the build process.


## Adding Widgets Tutorial
There are two kinds of widgets in `pcdswidgets`
1. Composite widgets, which start their lifecycles as standard `pydm` screens and are composed entirely of smaller standard widgets.
2. Symbol-based widgets, which start their lifecycles here in `pcdswidgets` and feature fully custom symbol components.

This tutorial will first go through how to add composite widgets, and then how to add symbol-based widgets. It is expected that most contributors will be adding composite widgets.

Along the way, we'll introduce concepts like naming and sizing rules as they become relevant.


### Why would I add a widget?
Before starting, consider why you might add a widget to `pcdswidgets`.
Some good reasons may be:

- Making a particularly useful or ubiquitous widget globally available and discoverable
- Making a high-usage widget easier to add to screens and control the settings of

The alternative is to pass your widget around via filepath and macros using `PyDMEmbeddedDisplay`,
which works great and may be sufficient for many use cases.


### Provisioning a Composite Widget
Before cloning this repo, you should create your widget as a `pydm` screen and try it out.
It will be simpler and faster to iterate on your design this way
and you can get immediate feedback without doing any library work.

If you don't know how to do this, refer to the `pydm` documentation:

- [PyDM Macro Substitution](https://slaclab.github.io/pydm/tutorials/intro/macros.html)
- [Creating a small (widget) ui file with macros](https://slaclab.github.io/pydm/tutorials/action/designer_inline.html)
- [Creating a screen that uses embedded displays](https://slaclab.github.io/pydm/tutorials/action/designer_main.html)

Before getting too deep, however, please consider widget sizing:


### Widget Sizing
We have some strict guidelines on widget sizing. These are established to give us some consistency in application of widgets, as well as to make it simpler to avoid resizing a widget between library releases.

Device control widgets should fall into exactly one of three size classes.
(Note: we can add more size classes if necessary).

To ensure sizing consistency, set the minimum and maximum sizes to values that look good throughout the range
and are permissible sizes as recorded below.
It's recommended to use fixed sizing when possible because dynamic sizing is hard to implement correctly.

Widgets should always be maintained to work at the original designed size, because changing this can break existing screens.

| Size Class | Width | Height |
| ---------- | ----- | -------|
| Full | 400 px | 125 px |
| Compact | 100 px | 75 px |
| Row | 800 px | 50 px |

Note:
- All widgets are allowed to be smaller than the maximum of their size class by up to 20%.
- Rows are also allowed to be double-height, e.g. 100px height.
- Widgets that aren't control widgets (containers, etc.) should not have a maximum or a minimum size. These widgets should instead be usable at any size. There is a list in the test suite to add test exceptions for these.


### Environment Setup
If you've gotten this far, with a provisioned widget of a good size class, it's time to set up your dev environment.
Before we begin, please clone the source code and make sure you can establish a working `designer` build
using the commands below.

Note that at LCLS this only works on Rocky 9 machines!

```
make
./try_in_designer.sh
```

If the `make` completes successfully, you will have a working `python` environment
and `try_in_designer.sh` will open a designer window with the existing `pcdswidgets` widgets in the sidebar.


### Adding Your Composite Widget: Part 1
1. Decide on your widget category: this is the subsystem and the type of the widget.
   - Example subsystems include "motion" and "vacuum".
   - Example types include "common", "smaract", and "beckhoff".

2. Copy your `.ui` file into `pcdswidgets` in the folder corresponding with your choices in step 1: `pcdswidgets/ui/${subsystem}/${type}`
   - Example: `pcdswidgets/ui/motion/beckhoff`
   - If this folder does not exist, consider if an existing folder is appropriate.
   - If no existing folder is appropriate, feel free to create a new folder.

3. Rename your `.ui` file to match the widget naming convention below.
   - It's important to be intentional about widget naming because renaming a widget can break existing screens.


### Widget Naming
Widget names and ui filenames should have one to one correspondence and contain three parts:

- Type of device controlled
- Descriptor word to differentiate this widget from other possible widgets with the same device type and size
- Size class signifier

For casing:
- `.ui` filenames should be lowercase_with_underscores for ease of working with filenames.
- Class names should use CamelCase to match qt and python naming conventions.
  - The class name will be generated automatically from the ui filename.

Examples:
- `motor_classic_full.ui` (`MotorClassicFull`)
   - Controls generic EPICS motor record
   - Is inspired by the classic EDM style
   - Is sized to be the "full" size
- `motor_tc_classic_row.ui` (`MotorTcClassicRow`)
   - Controls generic EPICS motor record with a thermocouple added
   - Is inspired by the classic EDM style
   - Is sized to be the "row" size

Other guidelines:

- The name should not be unnecessarily long, but avoid abbreviations.
- If multiple devices are controlled, include them in order of importance, e.g. `MotorTcClassicRow`.
- There is no need to end a widget name or filename with "Widget". Please avoid this.
- Widgets should never be renamed between tags, this will break existing screens.
- Widgets named before 2026 may break some of these rules because we don't want to rename them.


### Adding Your Composite Widget: Part 2
4. Run `make` to generate the code and update the project metadata.
   - This will generate at least three `.py` files and add a row to `pyproject.toml`.
   - Do not edit the files in `generated`.
5. Try it out!
   - Run `./try_in_designer.sh` and make a test screen. (Which, reminder: only works on rocky9 at LCLS).
   - After you've made a test screen, then do `./try_in_pydm.sh my_screen.ui` for further testing.
   - Make sure to take screenshots to include in your pull request.

At this point, if you like what you see, you're actually done.
You can commit, push, and make a pull request if you'd like.
The next few sections are optional.

Some notes:

- If you edit the ui file, you should `make` again, or your changes will not take effect.
- If you change your mind about which subsystem and type directory you'd like to use, you must manually delete the generated files from the old locations.


### Optional: Edit the Designer Settings
One of the built files is in `pcdswidgets/ui/${subsystem}/${type}`.

Unlike the files in `generated`, this file is free to edit,
and, among other things, contains a `DesignerOptions` specification for the widget.

This looks something like:

```
class MyClassFull(MyClassFullBase):
    designer_options = DesignerOptions(
        group="ECS Subsystem Type",
        is_container=False,
        icon=IconOptions.NONE,
    )
```

The editable options are:
- `group`, which determines which category the widget sorts into in the designer sidebar.
- `is_container`, which tells designer if we should be able to drag other widgets into this one in designer.
- `icon`, which tells designer which icon to use in the designer sidebar (see next section).


### Optional: Choose a Designer Icon
The designer icon is the symbol that appears to the left of the widget name in the left-hand widget box.
The default designer icon is simply the `Qt` logo. If you'd like to change it, you have a few options.

1. Use `IconOptions` (recommended)
   - `pydm` provides the free subset of fontawesome as icons.
   - You can select one of these by changing `IconOptions.NONE` to any of the other enum options.
   - If you're using an IDE, the options should autocomplete.
   - To see all of the options, run `show_icon_options.sh`. This will open up a grid with all of the options and names.

Here's an example:

```
class MyClassFull(MyClassFullBase):
    designer_options = DesignerOptions(
        group="ECS Subsystem Type",
        is_container=False,
        icon=IconOptions.expand_arrows_alt,
    )
```

2. Create your own `QIcon`
   - You can use the `Qt` APIs to create your own icon object.
   - For example: you can create an icon from a `.png`.
   - Please refer to the `Qt`/`PyQt` docs for how to do this.
   - You can set `icon=your_qicon_object` in your `DesignerOptions` to include your custom icon.


### Optional: Add Logic to a Composite Widget
The widget class here that includes the `designer_options` object is exactly the class that will be used
when your widget is included in a screen.
This means you can add code to the widget to override and extend any built-in behavior.

There are a few things to keep in mind when you do this:
1. If you override `__init__`, you must call `super().__init__(parent)` before doing any other `Qt`-related operations.
2. There is no way to pass custom arguments to `__init__` in `designer`.
   - Any parameterization should be done via `Qt` properties, which will show up in the sidebar.
   - If you do this, do not assume that the properties will be set in any particular order.
   - Make your code work regardless of which order the properties are set in.
3. Be wary of backwards compatibility.
   - Removing properties from a widget will break existing screens.

Here is an example where we add a single configuration parameter that does nothing. In practice, you would also change something meaningful about the widget during the setter.

```
try:
    from qtpy.QtCore import pyqtProperty
except ImportError:
    from qtpy.QtCore import Property as pyqtProperty  # type: ignore


class MyClassFull(MyClassFullBase):
    designer_options = DesignerOptions(
        group="ECS Subsystem Type",
        is_container=False,
        icon=IconOptions.NONE,
    )

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._my_value = 0

    def get_my_value(self) -> int:
        return self._my_value

    def set_my_value(self, value: int) -> None:
        self._my_value = value

    my_value = pyqtProperty(int, get_my_value, set_my_value)
```


### Composite Widget Limitations
- Widgets that contain `PyDMEmbeddedDisplay` are not supported: bootstrap these by turning the contents into widgets themselves.
- The automatic type hinting runs into issues when the qt object names are the same as the classnames. If you want to extend the composite widget class in python, giving your child widgets more unique names will result in more useful type hints, automatically.
- Only direct `QString` and `QStringList` properties are supported. We still need to implement support for item-based `QString` widgets such as `QListWidget`.
- The ordering of the designer widget categories is chaotic. This will require an update to `pydm` to resolve.
- In `pydm`, you can edit a ui file by hand and add a macro anywhere. This is not supported for composite widgets.


### Adding a Symbol-based Widget
This is how you would add e.g. a pump or valve widget with a custom drawing symbol and some color awareness.

This will require at least some familiarity with `Python`, `Qt`, `PyQt`, `pydm`, and with the structure of this module.

Largely: refer back to the existing widgets.

The steps are:

1. Create a new subclass of `BaseSymbolIcon` in the icons subfolder.
   - Define a path
   - Implement draw_icon
2. Create a new subclass of `PCDSSymbolBase`.
   - Include your icon as self.icon
   - Add relevant properties as needed, or inherit them from the existing mixins
   - include the `_qt_designer_` class attribute
3. `make`, to update `pyproject.toml` and the venv with new widget locations.

If the widget has been added and is included in the `pyproject.toml` file, it will appear in designer after installing `pcdswidgets`.

Note:
- At time of writing, all symbol-based widgets are vacuum widgets, and as such all the symbol-related code is in the vacuum folder.
  - If you would like to make a non-vacuum widget in this style, you should first refactor to pull out the base icon and symbol code, then edit the readme here to remove this note.
- The colors of all the existing vacuum symbol widgets is based on stylesheet rules. We keep the latest version of the stylesheet in use at LCLS in another module: see [lcls-twincat-vacuum](https://github.com/pcdshub/lcls-pydm-vacuum/blob/master/styleSheet/masterStyleSheet.qss).
  - You are not required to continue the stylesheet pattern if you add new symbol widgets.
