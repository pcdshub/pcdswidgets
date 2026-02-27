.PHONY: all clean

UI_SOURCE := $(wildcard pcdswidgets/builder/ui/*.ui)
PY_SOURCE := $(filter-out pcdswidgets/builder/ui/%.py, $(filter-out pcdswidgets/_version.py, $(shell find pcdswidgets -name "*.py")))
JINJA_SOURCE := $(wildcard pcdswidgets/builder/*.j2)

PY_FORM  := $(UI_SOURCE:.ui=_form.py)
PY_BASE   := $(UI_SOURCE:.ui=_base.py)

all: $(PY_FORM) $(PY_BASE) pyproject.toml

clean:
	rm $(PY_FORM)
	rm $(PY_BASE)

$(PY_FORM): $(UI_SOURCE) $(PY_SOURCE) $(JINJA_SOURCE)
	python -m pcdswidgets.builder.build uic $(@:_form.py=.ui)

$(PY_BASE): $(UI_SOURCE) $(PY_SOURCE) $(JINJA_SOURCE)
	python -m pcdswidgets.builder.build base $(@:_base.py=.ui)

pyproject.toml: $(PY_SOURCE)
	python -m pcdswidgets.entrypoint_widgets
