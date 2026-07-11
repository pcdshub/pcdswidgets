#!/bin/bash
# shellcheck disable=SC1091
#
# Runs pydm using widgets from the local .pixi
#
set -e
echo "try_in_pydm.sh is deprecated and will be removed in a future release." >&2
echo "Please use 'pixi run pydm' instead." >&2

THIS_DIR="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"
cd "${THIS_DIR}"

pixi run pydm "$@"
