.PHONY: all build venv venv-again

UI_SOURCE := $(wildcard pcdswidgets/ui/*/*/*.ui)
PY_SOURCE := $(filter-out pcdswidgets/builder/ui/%.py, $(filter-out pcdswidgets/_version.py, $(shell find pcdswidgets -name "*.py")))

PY_FORM := $(UI_SOURCE:pcdswidgets/ui/%.ui=pcdswidgets/generated/%_form.py)
PY_BASE := $(UI_SOURCE:pcdswidgets/ui/%.ui=pcdswidgets/generated/%_base.py)
PY_MAIN := $(UI_SOURCE:pcdswidgets/ui/%.ui=pcdswidgets/%.py)

all: venv build pyproject.toml venv-again

build: $(PY_FORM) $(PY_BASE) $(PY_MAIN)

# Need to re-run form and base if the ui file is updated
$(PY_FORM): pcdswidgets/generated/%_form.py: pcdswidgets/ui/%.ui
	.venv/bin/python -m pcdswidgets.builder.build uic $^

$(PY_BASE): pcdswidgets/generated/%_base.py: pcdswidgets/ui/%.ui
	.venv/bin/python -m pcdswidgets.builder.build base $^

# Only run if the target is missing: user can edit these
$(PY_MAIN):
	.venv/bin/python -m pcdswidgets.builder.build main $(@:pcdswidgets/%.py=pcdswidgets/ui/%.ui)

# Rerun if any python file is updated
pyproject.toml: $(PY_SOURCE)
	.venv/bin/python -m pcdswidgets.builder.entrypoint_finder

venv:
	./build_local_venv.sh

# For running again after pyproject.toml is regenerated
venv-again:
	./build_local_venv.sh
