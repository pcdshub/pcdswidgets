# Motor State Mover — usage

How to open the state mover screens with the repo's helper scripts. Both scripts
run from the local `.venv`, so build it first:

```bash
make venv
```

- `./try_in_pydm.sh` runs PyDM (runtime) from the `.venv`.
- `./try_in_designer.sh` runs Qt Designer with the pcdswidgets plugin loaded.

All screens are keyed by the **`DEVICE`** macro (the base prefix, e.g. `TST:D3`).
Macros are passed as JSON with `-m`; JSON is used because `MOTOR_TOKENS` contains
commas.

## PyDM (runtime)

### Plain state mover

```bash
./try_in_pydm.sh -m '{"DEVICE": "TST:D3"}' \
  pcdswidgets/ui/motion/common/motor_state_mover.ui
```

### Expert screen — standard (per-state configuration grid)

Needs `STATE_COUNT` (number of states) and `MOTOR_TOKENS` (comma-separated
per-motor tokens) for the Configuration tab; with only `DEVICE` you get the
Normal tab.

```bash
./try_in_pydm.sh -m '{"DEVICE": "TST:D3", "STATE_COUNT": 4, "MOTOR_TOKENS": "D1M1,D2M1,D3M1"}' \
  pcdswidgets/screens/motor_state_mover_expert.py
```

### Expert screen — PMPS variant

Set `PMPS` truthy (`"1"`, `"true"`, `"yes"`, `"on"`). The Configuration tab then
shows the PMPS controls (`arb_enable`, `maint_mode`) above the per-state motor
grid. Pass `STATE_COUNT` / `MOTOR_TOKENS` for the grid; with only `DEVICE` you
get just the PMPS controls.

```bash
./try_in_pydm.sh -m '{"DEVICE": "TST:D3", "PMPS": "1", "STATE_COUNT": 4, "MOTOR_TOKENS": "D1M1,D2M1,D3M1"}' \
  pcdswidgets/screens/motor_state_mover_expert.py
```

## Qt Designer (layout / editing)

Open Designer with the pcdswidgets widgets available in the widget box
(group **ECS Motion Common**):

```bash
./try_in_designer.sh
```

Open a specific `.ui` directly:

```bash
./try_in_designer.sh pcdswidgets/ui/motion/common/motor_state_mover.ui
```

Notes:

- The expert screens (`motor_state_mover_expert.py`) are Python `Display`s built
  in code — there is no `.ui`, so they open in PyDM only, not Designer.
- The `MotorStateMover`, `MotorStateMoverExpanded`, and
  `MotorStateMoverExpandedPMPS` widgets appear in the Designer widget box. Set
  their `device` property (and, for the expanded widgets, `stateCount` /
  `motorTokens`) via the widget's Core Properties editor (double-click the
  widget).
- The plain mover's **Expert Screen** button forwards `DEVICE` automatically;
  `STATE_COUNT`, `MOTOR_TOKENS`, and `PMPS` are inherited from the parent
  display's macros. So embedding the plain mover in a screen launched with those
  macros makes the button open the right expert variant.
