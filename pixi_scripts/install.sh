#!/bin/bash
# shellcheck disable=SC1091
# Set up designer plugin for including Python widgets

set -e

HERE="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"
THIS_ENV="${HERE}"/..
DEST="${THIS_ENV}"/.pixi/envs/default/plugins/designer/libpyqt5.so

if [ -f "${DEST}" ]; then
    exit 0
fi

PLUGIN=/cds/group/pcds/pyps/conda/designer_fix/3_12/libpyqt5.so
cp "${PLUGIN}" "${DEST}"
