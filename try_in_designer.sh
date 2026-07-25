#!/bin/bash
# shellcheck disable=SC1091
#
# Runs designer using widgets from the local .pixi
#
set -e
echo "try_in_designer.sh is deprecated and will be removed in a future release." >&2
echo "Please use 'pixi run designer' instead." >&2

THIS_DIR="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"
cd "${THIS_DIR}"

pixi run designer "$@" 2>/dev/null
