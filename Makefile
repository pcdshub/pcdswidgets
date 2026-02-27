.PHONY: all clean

UI_SOURCE := $(wildcard pcdswidgets/builder/ui/*.ui)
PY_FORMS  := $(UI_SOURCE:.ui=_form.py)
PY_BASE   := $(UI_SOURCE:.ui=_base.py)

all: $(PY_FORMS) $(PY_BASE) pyproject.toml

clean:
	rm $(PY_FORMS)
	rm $(PY_BASE)

$(PY_FORMS): $(UI_SOURCE) $(wildcard pcdswidgets/builder/*.py) $(wildcard pcdswidgets/builder/*.j2)
	python -m pcdswidgets.builder.build uic $(@:_form.py=.ui)

$(PY_BASE): $(UI_SOURCE) $(wildcard pcdswidgets/builder/*.py) $(wildcard pcdswidgets/builder/*.j2)
	python -m pcdswidgets.builder.build base $(@:_base.py=.ui)

pyproject.toml: $(shell find . -name "*.py")
	python -m pcdswidgets.entrypoint_widgets
