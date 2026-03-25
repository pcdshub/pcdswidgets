#!/bin/bash
# shellcheck disable=SC1091
#
# Runs pydm using widgets from the local .venv
#
set -e

THIS_DIR="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"
cd "${THIS_DIR}"

source base_env_vars.sh
source .venv/bin/activate

pydm "$@"
