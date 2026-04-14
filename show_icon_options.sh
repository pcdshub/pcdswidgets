#!/bin/bash
# shellcheck disable=SC1091
#
# Open a window with all built-in designer icon options.
#
set -e

THIS_DIR="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"
cd "${THIS_DIR}"

unset PYTHONPATH
source base_env_vars.sh
source .venv/bin/activate

python -m pcdswidgets.builder.get_icon_options show
