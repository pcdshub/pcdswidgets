#!/bin/bash
HERE="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"
THIS_ENV="${HERE}"/..

export PYQTDESIGNERPATH="${THIS_ENV}"/.pixi/envs/default/lib/python3.12/site-packages/pydm
export PYDM_DESIGNER_ONLINE=1
export QT_XCB_GL_INTEGRATION=none
