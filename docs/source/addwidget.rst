==========================
Adding a New Vacuum Widget
==========================

This page details the development process for adding a new vacuum widget.
It was made during the process of creating the PneumaticValveDA widget.


Requirements
------------
You should have the following things in mind before you begin:

- What should the widget look like?
- Is there any existing widget that this is similar to?
- What are my interlock, error, state readback, and control PVs?


Implementation Overview
-----------------------
You'll need to do the following things:

- Add a new icon widget.
- Add a new valve widget that uses the icon.
- Add a new device class for your widget's expert screen.
- Update stylesheets to be consistent for your new widget.


Adding a New Icon Widget
------------------------
The icon widgets are stored in pcdswidgets/icons and are implemented by
using the QtGui painter tools. I suggest you pick a class that almost
does what you want as a starting point.
With BaseSignalIcon as a parent class, the only method you need to override
is "draw_icon". Check out the other icons for examples and feel free to
browse the qt documentation.
This process will take a lot of iterations
(edit the file, check the ui, repeat).
To make this process smoother, I added a script embedded in the icons module.
Try this to open an application that simply displays a widget:

.. code-block bash
   python -m pcdswidgets.icons.demo ControlValve

Some tips:

- The coordinate system starts from the top left of the icon, so positive y is down
- The expected size of the widget icon is from 0 to 1 in both x and y
- If you want something to be modifyable via stylesheet, PV, etc., you can make it
  a property with qt's @Property flag. This is useful for alarm sensitive coloring,
  for example.
- When drawing a shape, it's useful to parameterize it even if you only use it once.
  This is because you may later want to edit the specifics, but if your QPolygon
  is just a list of numbers this will be very hard. A list of variables like
  "arrow_length" are easier to modify later.


Adding a New Widget Class
-------------------------
Widget classes in pcdswidgets are constructed from a network of mix-ins and parent
classes. A good place to start is simply copying the most similar existing
widget and modifying the specifics to match yours. Barring something extremely
similar existing, you'll need to delve into the specifics of the inner workings
and I can't encapsulate that in a guide.

In some cases, you may be able to get away with simply copying a widget
and changing the docstrings, attributes, and super calls as appropriate.

For deeper dives, I recommend looking at each mix-in class in isolation to
understand how that particular feature is implemented.