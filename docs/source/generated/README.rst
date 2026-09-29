pcdswidgets
===========

This is a widget library that uses the ``pydm`` framework to add
additional widgets to the ``pydm`` ecosystem.

When ``pcdswidgets`` is installed in a ``python`` environment, it will
provide:

- Additional widgets in ``designer`` via ``pydm``\ ’s widget entrypoint.
- The same additional widgets at runtime for use in ``pydm`` and
  ``PyQt`` displays.
- A cli interface, ``pcdswidgets-show``, for showing standalone windows
  with screens and widgets sourced from the module. (For example: to
  open an expert screen standalone that would otherwise be embedded
  within a widget). See ``pcdswidgets-show`` for more details, including
  help and usage.

At ``LCLS``, this is pre-installed on all environments that provide
``designer``.

It is distributed via both ``pypi`` and ``conda-forge``, so it is
installable with ``pip``, ``conda``, ``uv``, and ``pixi``.

See the `complete docs <https://pcdshub.github.io/pcdswidgets>`__ for
more information.
