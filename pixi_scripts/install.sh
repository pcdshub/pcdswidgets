#!/bin/bash
# shellcheck disable=SC1091
# Set up designer plugin for including Python widgets

set -e

HERE="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"
THIS_ENV="${HERE}"/..

PLUGIN=/cds/group/pcds/pyps/conda/designer_fix/3_12/libpyqt5.so

for envname in default typhos; do
    dest_dir="${THIS_ENV}"/.pixi/envs/"${envname}"/plugins/designer
    dest="${dest_dir}"/libpyqt5.so

    if [ -f "${dest}" ]; then
        echo "Skip designer plugin install in ${envname} environment: already installed."
        continue
    fi
    if [ -d "${dest_dir}" ]; then
        echo "Installing designer plugin in ${envname} environment."
    else
        echo "Skip designer plugin install in ${envname} environment: env does not exist yet."
        continue
    fi

    cp "${PLUGIN}" "${dest}"
done
