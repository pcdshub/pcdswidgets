#!/bin/bash
# shellcheck disable=SC1091
#
# Runs designer using widgets from the local .venv
#
set -e

THIS_DIR="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"
cd "${THIS_DIR}"

unset PYTHONPATH
source base_env_vars.sh
source .venv/bin/activate
PYVER="$(cat .python-version)"
export PYQTDESIGNERPATH=".venv/lib/python${PYVER}/site-packages/pydm"
export PYDM_DESIGNER_ONLINE=1

"${BASE_ENV}/bin/designer" "$@"
