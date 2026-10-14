============================
CameraViewerStretch
============================

``CameraViewerStretch`` is a top-level AreaDetector viewer that combines the live
image display with a collapsible sidebar. It is meant to act as a container: any
widgets dropped into it are adopted into the sidebar on first show and wrapped in
collapsible sections for organization.

This makes it useful for building a camera-specific control panel where the main
preview remains visible while auxiliary controls are kept in a hidable side panel.

Overview
--------

- The widget displays the live image stream from an AreaDetector plugin.
- The sidebar is hidden by default until widgets are adopted or the toggle is
  enabled.
- Adopted child widgets inherit the parent camera context, including the active
  ``cam_prefix`` and stream plugin information.
- The widget can be oriented either horizontally or vertically via the
  ``orientation`` property, which controls how the sidebar sits relative to the
  preview.

Important macros and properties
------------------------------

``cam_prefix``
    The base prefix for the camera PVs, such as ``IOC:CAM:``. This is the main
    camera identifier used by the image view and is propagated to adopted child
    widgets so they point at the same detector.

``nickname``
    The text displayed at the top of the widget. This is the visible name shown
    in the title/header area of the viewer.

``stream_plugin``
    The AreaDetector stream plugin being displayed. The default is
    ``:IMAGE1:`` and it includes the conventional leading and trailing colons so
    the full stream PV can be changed cleanly while keeping the plugin name
    structure intact.

``img_protocol``
    The protocol used for the stream PV, typically ``ca://`` by default. This is
    appended in front of the image PV address and is useful when switching to
    ``pva://`` for a PVA-based stream.

``suffix_waveform_channel``
    The waveform field suffix used by the image source. The default is
    ``ArrayData`` for the standard CA-based workflow.

``suffix_width_channel``
    The width field suffix used by the image source. The default is
    ``ArraySize0_RBV`` for CA-based streams. This is mainly relevant for the
    width source when the image plugin is not using the standard CA naming
    convention; for PVA the width does not need to be matched the same way.

Sidebar behavior
----------------

The sidebar is designed to hold camera-specific controls and other widgets that
should stay grouped with the preview. When widgets are dropped into the container,
``CameraViewerStretch`` detects them and adopts them into a collapsible sidebar
section on first show. The toggle button can hide or show the sidebar as needed.

The title shown at the top of each collapsible section is taken from the adopted
child widget's ``nickname`` property. In other words, the section header is the
sub-widget's ``nickname`` label, not a separate viewer label. If a widget is
being set up in Designer and does not already expose a ``nickname`` property, add
it as a dynamic property so the sidebar title can be customized.

The order of adopted widgets in the sidebar is determined by the original widget
positions in the design, using their ``y`` coordinate. In practice, placement
otherwise has no effect on the final sidebar ordering. This can look a bit ugly
in the Designer preview when a large number of widgets are present, but the final
runtime layout is still sorted by that coordinate.

The sidebar layout can be oriented relative to the preview using the
``orientation`` property:

- ``Qt.Horizontal``: preview and sidebar sit side-by-side.
- ``Qt.Vertical``: preview and sidebar are stacked in the other direction.



.. automodule:: pcdswidgets.imaging.common.camera_viewer_stretch
.. autoclass:: CameraViewerStretch
    :members:
