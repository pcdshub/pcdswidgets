#!/bin/bash
#
# Local environment settings for building/testing at LCLS
#

# Disable GL because it crashes on our servers
QT_XCB_GL_INTEGRATION=none
# Pick a base env that has designer configured appropriately and built to match python + pyqt versions
BASE_ENV="${PYPS_SITE_TOP}/conda/dev/zlentz/miniforge3/envs/ecs-base-0.0.3"

export QT_XCB_GL_INTEGRATION
export BASE_ENV
