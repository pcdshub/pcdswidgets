============================
EtherCAT Widgets
============================

Widgets to view the EtherCAT terminals of a Beckhoff PLC and request state changes,
using the PVs pytmc generates for every terminal (``{prefix}ECAT:{port}:...``).

These are in the `ECS Common Ethercat` group in the designer widgets box.

.. toctree::
    :maxdepth: 1

    ethercat_terminal_states_stretch.rst
    ethercat_terminal_state_double_row.rst


Overview
--------

- :any:`EthercatTerminalStatesStretch` shows every terminal of one PLC as a tree that
  follows the EtherCAT wiring (master line, junction Port branches, Hot Connect groups).
  Each group row shows the worst status below it. Selecting a terminal shows it in an
  :any:`EthercatTerminalStateDoubleRow` panel.
- :any:`EthercatTerminalStateDoubleRow` shows one terminal and requests state changes.
- The ``ethercat_terminal_states`` screen wraps the tree widget for ``pcdswidgets-show``::

      pcdswidgets-show ethercat_terminal_states --PLC plc-sds-raptor --PREFIX PLC:ICL:IOC:

  Macros: ``PLC`` and ``PREFIX`` (required), ``DISCOVERY`` (discovery file),
  ``CONFIRM`` (``0`` = no confirmation before state requests).

Designer properties:

=================================  ===================================================
Widget                             Properties
=================================  ===================================================
EthercatTerminalStatesStretch      ``plc``, ``prefix``, ``discoveryFile``, ``confirmRequests``
EthercatTerminalStateDoubleRow     ``prefix``, ``port``, ``terminal_name``, ``terminal_type``,
                                   ``confirmRequests``
=================================  ===================================================

``prefix`` is the IOC prefix including the trailing colon (e.g. ``PLC:ICL:IOC:``);
``port`` is the EtherCAT address of the terminal (e.g. ``1015``).


Status: PVs
-----------

Each terminal is followed through these PVs. Updates are pushed by Channel Access
(no polling); the widgets repaint when they arrive.

==================  ======  =====  ==============================================
PV                  Type    RO/RW  Meaning
==================  ======  =====  ==============================================
``State_RBV``       mbbi    RO     INIT / PREOP / BOOTSTRAP / SAFEOP / OP
``Link_RBV``        mbbi    RO     OK / NOT_PRESENT / ... / MULTIPLE_FLAGS
``State_SP``        mbbo    RW     requested state (same enum as ``State_RBV``)
``State_SP.DISP``   field   RO     1 = Channel Access puts disabled
``State_SP.DISA``   field   RO     record disabled when DISA == DISV
``State_SP.DISV``   field   RO
``StateRaw``        longin  RO     raw state word: flags in bits 4-7 (pytmc helper)
``LinkCode``        calc    RO     link conditions bits 0-3, ports bits 4-7 (helper)
==================  ======  =====  ==============================================

A terminal is OK when it is in OP, its link is OK and no state flag (e.g. ERROR) is
set. In the tree, a grey dot means OK, a red dot a fault and a dashed ring
disconnected; the "Show" filter selects All terminals, Faults, Not OP, Link not OK,
Editable or Disconnected.


Access and state requests
-------------------------

A terminal is **EDITABLE** when ``State_SP.DISP == 0``, ``DISA != DISV`` and Channel
Access grants write access (the record semantics, as in pytmc
``effective_access()``). Otherwise it is **LOCKED**, and the Access tooltip lists the
reasons. State changes can only be requested for an editable terminal:

1. the user picks a state in the Request combo box;
2. a confirmation dialog asks first (unless ``confirmRequests`` is off);
3. access is checked again right before ``State_SP`` is written, since PVs keep
   updating while the dialog is open. If the terminal became locked, nothing is
   written and the selection goes back.

In a read-only PyDM session (Qt Designer, ``pydm --read-only``) Channel Access reports
no write access for every PV, so write access is ignored when showing EDITABLE /
LOCKED, and requests are disabled.


Discovery: the terminal list
----------------------------

The tree needs the PLC's terminals and how they are wired. This comes from a
discovery file, written by a read-only wrapper around ``ads-actions``. Discovery only
runs when the user asks: the **Rediscover** button of the tree widget, or the command
line::

    ctrlenv-pathmunge ads-actions
    python -m pcdswidgets.common.ethercat.discover plc-sds-raptor
    python -m pcdswidgets.common.ethercat.discover plc-sds-raptor -o /some/dir/

- It runs ``ads read-ecat-topology`` only, and refuses any other ``ads`` command.
- Default file: ``~/.cache/ecat-states/<plc>.json`` (``$XDG_CACHE_HOME`` is honoured).
  ``discoveryFile`` / ``-o`` may name a file or a directory (then ``<dir>/<plc>.json``);
  missing directories are created. If that location is not writable, Rediscover
  writes to the user cache instead.
- Other options: ``--ethercat-master-ams-net-id`` (default: resolved by ads-actions)
  and ``--timeout`` (seconds, default 300).
- ads-actions is found through ``$ADS_ACTIONS_BIN`` first, then ``ads`` on ``PATH``,
  then the released install location.

Without a discovery file the tree explains how to create one.
