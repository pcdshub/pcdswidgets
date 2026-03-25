.PHONY: all build clean venv

UI_SOURCE := $(wildcard pcdswidgets/builder/ui/*.ui)
PY_SOURCE := $(filter-out pcdswidgets/builder/ui/%.py, $(filter-out pcdswidgets/_version.py, $(shell find pcdswidgets -name "*.py")))
JINJA_SOURCE := $(wildcard pcdswidgets/builder/*.j2)

PY_FORM  := $(UI_SOURCE:.ui=_form.py)
PY_BASE   := $(UI_SOURCE:.ui=_base.py)

all: build pyproject.toml

# make build is for pip, etc. so pyproject.toml doesn't change at build time
build: $(PY_FORM) $(PY_BASE)

clean:
	rm $(PY_FORM)
	rm $(PY_BASE)

$(PY_FORM): $(UI_SOURCE) $(PY_SOURCE) $(JINJA_SOURCE)
	python -m pcdswidgets.builder.build uic $(@:_form.py=.ui)

$(PY_BASE): $(UI_SOURCE) $(PY_SOURCE) $(JINJA_SOURCE)
	python -m pcdswidgets.builder.build base $(@:_base.py=.ui)

pyproject.toml: $(PY_SOURCE)
	python -m pcdswidgets.entrypoint_widgets

venv:
	./build_local_venv.sh
