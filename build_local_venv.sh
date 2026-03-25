#!/bin/bash
# shellcheck disable=SC1091
#
# This is the script we run on "make venv"
#
# Builds a .venv with a local install of pcdswidgets and working designer plugin.
# This can be re-run to update the pcdswidgets install, e.g. if you added a new widget.
# If you change the base environment, you'll have to remove and rebuild the .venv
#
set -e

THIS_DIR="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"
cd "${THIS_DIR}"

source base_env_vars.sh
PYTHON_EXE="${BASE_ENV}/bin/python"

# Two paths: can specify uv or venv as an input arg
# Or, I will default to uv if it's on your path, venv otherwise
if [[ "$1" == "uv" ]]; then
    MODE="uv"
elif [[ "$1" == "venv" ]]; then
    MODE="venv"
elif command -v "uv"; then
    MODE="uv"
else
    MODE="venv"
fi

if [[ "$MODE" == "uv" ]]; then
    if [[ ! -d ".venv" ]]; then
        echo "Building new .venv using uv"
        uv venv --system-site-packages --python "$PYTHON_EXE" .venv
    fi
    echo "Updating .venv using uv"
    uv sync --extra dev --extra doc --extra test
elif [[ "$MODE" == "venv" ]]; then
    if [[ ! -d ".venv" ]]; then
        echo "Building new .venv using venv module"
        "$PYTHON_EXE" -m venv --system-site-packages .venv
    fi
    source .venv/bin/activate
    echo "Updating .venv using pip"
    pip install -e '.[dev,doc,test]'
else
    echo "Unhandled mode ${MODE}"
fi
