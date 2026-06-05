#!/bin/bash
# shellcheck disable=SC1091
#
# Runs designer using widgets from the local .pixi
#
set -e

THIS_DIR="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"
cd "${THIS_DIR}"

pixi run --as-is designer "$@" 2>/dev/null
